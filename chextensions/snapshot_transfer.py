import os
import shutil
import tarfile
import tempfile
import yaml
from datetime import datetime as dt
from glob import glob
from google.cloud import storage
from chainer.training import extension


def snapshot_transfer(keys, path):
    @extension.make_extension(trigger=(1, 'epoch'), priority=-200)
    def snapshot_transfer(trainer):
        _snapshot_transfer(trainer, keys, path)

    return snapshot_transfer


def _snapshot_transfer(trainer, keys, config_path):
    config = yaml.load(open(config_path))
    gcs_client = storage.Client.from_service_account_json(
        config['key-file'], project=config['project'])
    bucket = gcs_client.get_bucket(config['bucket'])
    model_name = trainer.updater._optimizers['main'].target.__class__.__name__

    targets = [_get_latest_modified_object(trainer.out, k) for k in keys]

    prefix = model_name + dt.now().strftime('%y%m%d%H%M') + '_'
    with tempfile.TemporaryDirectory(prefix=prefix, dir=trainer.out) as tmp_path:
        for f in filter(lambda x: x is not None, targets):
            shutil.copyfile(f, os.path.join(tmp_path, os.path.basename(f)))
        out_tar = tmp_path + '.tar.gz'
        with tarfile.open(out_tar, mode='w:gz') as tar:
            tar.add(tmp_path, arcname=os.path.basename(tmp_path))

        dst = os.path.join(config['dst'], os.uname()[1], os.path.basename(out_tar))
        blob = bucket.blob(dst)
        try:
            blob.upload_from_filename(out_tar)
        except Exception as e:
            print(e)
        os.remove(out_tar)


def _get_latest_modified_object(dirname, key):
    target = os.path.join(dirname, '%s*' % key)
    files = [(f, os.path.getmtime(f)) for f in glob(target)]
    if len(files) == 0:
        return
    latest = sorted(files, key=lambda x: x[1])[-1]
    return latest[0]

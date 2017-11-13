import hashlib
import os
import slackweb
import yaml
from google.cloud import storage
from chainer.training import extension

def slack_report(keys, hook, channel, config_path=None):
    @extension.make_extension(trigger=(1, 'epoch'), priority=0)
    def slack_report(trainer):
        _slack_report(trainer, keys, hook, channel, config_path)

    return slack_report

def _slack_report(trainer, keys, hook, channel, config_path):
    slack = slackweb.Slack(url=hook)
    updater = trainer.updater
    model_name = updater._optimizers['main'].target.__class__.__name__
    log_report = trainer.get_extension('LogReport')
    current_log = log_report.log[-1]

    attachments = list()

    fields = list()
    color = 'good'
    for k in keys:
        if k in current_log:
            fields.append({'title': k, 'value': current_log[k], 'short': True})
            if not (isinstance(current_log[k], float) or isinstance(current_log[k], int)):
                color = 'danger'
                # mention
    attachments.append(
        {'pretext': model_name, 'color': color, 'fields': fields})

    if config_path is not None:
        plot_reports = [v.extension for k, v in trainer._extensions.items() if 'PlotReport' in k]
        if len(plot_reports) > 0:
            config = yaml.load(open(config_path))
            client = storage.Client.from_service_account_json(
                config['key-file'], project=config['project'])
            bucket = client.get_bucket(config['bucket'])

            for pr in plot_reports:
                name = pr._file_name
                if os.path.isfile(os.path.join(trainer.out, name)):
                    url = _upload_figure(name, trainer.out, bucket, config['figure-uri'])
                    attachments.append(
                        {'color': color, 'image_url': url, 'fields': [{'value': name}]})

    slack.notify(channel=channel,
        text='Training Report from %s' % os.uname()[1],
        attachments=attachments)

def _upload_figure(name, out, bucket, figure_uri):
    path = os.path.join(out, name)

    with open(path, 'rb') as f:
        chsum = hashlib.md5(f.read()).hexdigest()
    dst = os.path.join(figure_uri, chsum + '.png')
    blob = bucket.blob(dst)
    blob.upload_from_filename(path)
    blob.make_public()

    return blob.public_url

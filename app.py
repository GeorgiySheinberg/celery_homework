import os
import uuid

from celery import Celery, Task
from celery.result import AsyncResult
from flask import Flask, request
from flask import jsonify, send_from_directory
from flask.views import MethodView

from upscale import upscale


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


app = Flask(__name__)
app.config.from_mapping(
    CELERY=dict(
        broker_url="redis://localhost",
        result_backend="redis://localhost",
        broker_connection_retry_on_startup=True
    ),
)
celery_app = celery_init_app(app)

@celery_app.task()
def upscale_photo(image_path):
    upscale(image_path, f'{image_path[:-4]}_upscaled{image_path[-4:]}')
    return


class Comparison(MethodView):

    def get(self, task_id):
        task = AsyncResult(task_id, app=celery_app)
        return jsonify({'status': task.status,
                        'result': task.result})

    def post(self):
        image_path = self.save_image('image_1')
        task = upscale_photo.delay(image_path)
        file_name = f'{image_path[:-4]}_upscaled{image_path[-4:]}'
        return jsonify(
            {
             'task_id': task.id,
             'file_name': file_name.replace('files/', "")
             }
        )

    def save_image(self, field):
        image = request.files.get(field)
        extension = image.filename.split('.')[-1]
        path = os.path.join('files', f'{uuid.uuid4()}.{extension}')
        image.save(path)
        return path

@app.route('/processed/<filename>')
def download(filename):
    return send_from_directory('files', filename, as_attachment=True)


comparison_view = Comparison.as_view('comparison')
app.add_url_rule('/tasks/<task_id>', view_func=comparison_view, methods=['GET'])
app.add_url_rule('/upscale', view_func=comparison_view, methods=['POST'])

if __name__ == '__main__':
    app.run()
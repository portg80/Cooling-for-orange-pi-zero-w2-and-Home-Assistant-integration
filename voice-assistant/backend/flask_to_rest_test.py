from flask import Flask, render_template, request
from flask_restful import Api, Resource, reqparse
#https://www.youtube.com/watch?v=VfkTcR4J3Y4
app = Flask(__name__)
api = Api()

courses = {
    1 : {"name": "Python", "videos":  15},
    2 : {"name": "Rest Api", "videos":  98},
    3 : {"name": "3D Max", "videos":  21},
}

parser = reqparse.RequestParser()
parser.add_argument("name", type=str)
parser.add_argument("videos", type=int)

class Main(Resource):
    def get(self, course_id):
        if course_id == 0:
            return courses
        else:
            return courses[course_id]

    def delete(self, course_id):
        del courses[course_id]
        return courses

    def post(self, course_id):
        courses[course_id] = parser.parse_args()
        return courses

    def put(self, course_id):
        courses[course_id] = parser.parse_args()
        return courses

api.add_resource(Main, "/api/courses/<int:course_id>")
api.init_app(app)


@app.route('/api/start_porno')
def index():
    print("ПОРНО ЗАПУЩЕНО")
    return "done"


if __name__ == '__main__':
    print("[SERVER] Flask сервер запущен на http://127.0.0.1:3000")
    app.run(host='127.0.0.1', port=3000, debug=True)

"""Read-only problem catalog endpoints."""

from flask_restx import Namespace, Resource

from pages.problem_data import PROBLEMS


api = Namespace("problems", description="题库相关接口")

SUMMARY_FIELDS = (
    "id",
    "sourceNumber",
    "category",
    "categoryLabel",
    "title",
    "difficulty",
    "tags",
    "interactive",
    "judgeable",
    "timeLimit",
    "memoryLimit",
)


def serialize_summary(problem):
    summary = {key: problem.get(key) for key in SUMMARY_FIELDS}
    summary["category"] = summary["category"] or "general"
    summary["categoryLabel"] = summary["categoryLabel"] or "通用题库"
    summary["interactive"] = bool(summary["interactive"])
    summary["judgeable"] = summary["judgeable"] is not False
    return summary


def serialize_problem(problem):
    data = dict(problem)
    data.setdefault("category", "general")
    data.setdefault("categoryLabel", "通用题库")
    data.setdefault("interactive", False)
    data.setdefault("judgeable", True)
    return data


@api.route("")
class ProblemListController(Resource):
    @api.doc("list_problems")
    def get(self):
        problems = [serialize_summary(PROBLEMS[problem_id]) for problem_id in sorted(PROBLEMS)]
        return {"data": problems, "total": len(problems)}, 200


@api.route("/<int:problem_id>")
class ProblemDetailController(Resource):
    @api.doc("get_problem")
    def get(self, problem_id):
        problem = PROBLEMS.get(problem_id)
        if problem is None:
            return {"error": "题目不存在"}, 404
        return serialize_problem(problem), 200

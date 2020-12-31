from django.contrib.admin import ModelAdmin, register
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin
from . import models


@register(models.Problem)
class ProblemAdmin(ModelAdmin):
    list_display = ("id", "index", "name", "statement_begin", "max_score")

    def statement_begin(self, problem):
        if len(problem.statement) > 5:
            return problem.statement[:50] + "..."
        return problem.statement

    statement_begin.short_description = "statement"


@register(models.Contest)
class ContestAdmin(ModelAdmin):
    list_display = ("id", "name", "start_time", "finish_time")


@register(models.Solution)
class SolutionAdmin(ModelAdmin):
    list_display = ("id", "user", "problem", "is_correct", "score", "created_at")
    list_filter = ("problem", "is_correct")


@register(models.CloseSubmissionSabotage)
@register(models.SolveTaskSabotage)
class AbstractSabotageChildAdmin(PolymorphicChildModelAdmin):
    pass


@register(models.AbstractSabotage)
class AbstractSabotageAdmin(PolymorphicParentModelAdmin):
    base_model = models.AbstractSabotage
    child_models = (models.CloseSubmissionSabotage, models.SolveTaskSabotage)

    list_display = ("id", "get_type", "contest", "user", "start_time", "finish_time")

    def get_type(self, sabotage: models.AbstractSabotage):
        return sabotage.get_real_instance_class().__name__
    get_type.short_description = "type"


@register(models.SabotageSolution)
class SabotageSolutionAdmin(ModelAdmin):
    list_display = ("id", "contest", "sabotage", "user", "answer", "is_correct")
    list_filter = ("contest", "is_correct")

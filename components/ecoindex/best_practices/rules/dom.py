from ecoindex.best_practices.context import BestPracticesContext
from ecoindex.best_practices.models import CheckOutcome, RuleDefinition
from ecoindex.best_practices.registry import register


@register("externalize_css_js")
def check_externalize_css_js(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    value = float(context.dom.inline_js + context.dom.inline_css)
    return CheckOutcome(
        value=value,
        message=(
            f"{int(value)} inline CSS/JavaScript block(s) "
            f"({context.dom.inline_css} CSS, {context.dom.inline_js} JS)"
        ),
    )


@register("print_stylesheet")
def check_print_stylesheet(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    value = float(context.dom.print_stylesheet)
    if value >= 1:
        message = f"{int(value)} print stylesheet(s) found"
    else:
        message = "No print stylesheet found"
    return CheckOutcome(value=value, message=message)

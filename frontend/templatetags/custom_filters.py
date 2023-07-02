from django import template

register = template.Library()

@register.filter
def weiToEth(value):
    try:
        return float(value) / 10**18
    except:
        return 0


@register.filter
def gweiToEth(value):
    try:
        res = float(value) / 10**18
        return round(res, 5)
    except:
        return 0
    

@register.filter
def commaSeparatorNumber(value):
    try:
        return f'{value:,}'
    except:
        return "0"
from django import template

register = template.Library()

@register.filter
def weiToEth(value):
    try:
        return float(value) / 10**18
    except:
        return 0


@register.filter
def weiToEthRound(value):
    try:
        res = float(value) / 10**18
        return round(res, 5)
    except:
        return 0


@register.filter
def gweiToEthRound(value):
    try:
        res = float(value) / 10**9
        return round(res, 5)
    except:
        return 0
    

@register.filter
def commaSeparatorNumber(value):
    try:
        return f'{value:,}'
    except:
        return "0"
    

@register.filter
def elide_string(string):
    if len(string) <= 12:
        return string
    else:
        return string[:4] + "..." + string[-5:]
    

@register.filter
def hex_to_string(value):
    try:
        hex_value = value[2:]  # Remove '0x' prefix
        byte_string = bytes.fromhex(hex_value)
        return byte_string.rstrip(b'\x00').decode('utf-8')  # Remove trailing zeros and decode
    except:
        return None
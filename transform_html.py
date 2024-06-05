import typing
import pydash
import re
from bs4 import BeautifulSoup

import logging as lg
logging = lg.getLogger('transform_html')

class ParserTransfromRule(typing.TypedDict, total=False):
    selector: str
    mapping: str
    attribute_name: str
    regex_sub_value: list[str]
    children: 'ParserTransfromRule'
    grouping: str
    exception_on_not_found: bool

def transform_html(
        transformed_data: 'dict | list', 
        soup: 'BeautifulSoup | str', 
        rule: 'ParserTransfromRule | list',
        level: int = 1,
        limit: int = 1000,
        parser_impl = "lxml" # "html.parser", lxml c-lang impl for large files
    ):
    logging.debug(f'{level} {rule}')
    if level > limit:
        raise RecursionError(f'level [{level}] greater than limit [{limit}]')

    def handle_regex(rx, text):
        return re.sub(rx[0], rx[1], text, flags=re.DOTALL)
    def handle_attr(selected_soup, attr_name):
        return selected_soup.get(attr_name)
    
    selected_soup = BeautifulSoup(soup, features=parser_impl) if type(soup) is str else soup
    transformed_data_out = transformed_data
    
    if type(rule) is list:
        [ transform_html(transformed_data, selected_soup, r, level=level+1) for r in rule ]
        return
    
    if rule.get('grouping') and type(transformed_data) is not list:
        transformed_data_out = transformed_data
        
    if rule.get('grouping') and type(transformed_data) is list:
        transformed_data_out = {} 
        transformed_data.append(transformed_data_out)
    

    if rule.get('selector'):
        tags = selected_soup.select( rule['selector'] )
        if not tags and not rule.get('exception_on_not_found'):
            return
        if not tags:
            msg = f'None found at all by selector "{rule["selector"]}"'
            logging.debug(f'{msg} \n {selected_soup} \n {rule}')
            raise LookupError(msg)
        if len(tags) > 1 and type(transformed_data_out) is list:
            [ transform_html(transformed_data_out, s, rule | { 'selector': None}, level=level+1) for s in  tags]
            return
        if len(tags) > 1:
            nested_data = []
            [ transform_html(nested_data, s, rule | { 'selector': None}, level=level+1) for s in  tags]
            key_name = rule.get('grouping') or rule.get('mapping')
            if key_name:
                pydash.objects.set_(transformed_data_out, key_name, nested_data)
            return
        selected_soup = tags[0]

    mapping = rule.get('mapping') or ( 
                rule.get('grouping') if not rule.get('children') else None 
              ) 
    if mapping:
        attr_name = rule.get('attribute_name') or 'text'
        text = selected_soup.text if attr_name == 'text' else handle_attr(selected_soup, attr_name)
        text = (text or '').strip()
        handled_text = handle_regex(rule['regex_sub_value'], text) if rule.get('regex_sub_value') else text
        
        if type(transformed_data_out) is dict:
            pydash.objects.set_(transformed_data_out, mapping, handled_text)
    
        if type(transformed_data_out) is list:
            transformed_data_out.append(handled_text)
        
    if rule.get('children'):
        transform_html(transformed_data_out, selected_soup, rule['children'], level=level+1)

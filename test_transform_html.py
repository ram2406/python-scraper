import unittest
import logging
import json
from bs4 import BeautifulSoup
import transform_html as th
import os
import yaml

# logging.getLogger().setLevel(10)
class Test_TransformHTML(unittest.TestCase):
    
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.rule = [
            th.ParserTransfromRule(
                selector='.tc1', mapping='firstResult'
            ),
            th.ParserTransfromRule(
                selector='div[attr="1"]', mapping='secondResult'
            ),
            th.ParserTransfromRule(
                selector='div div div', mapping='thridResult', grouping='checked',
            ),
            th.ParserTransfromRule(
                selector='div div div', grouping='checked2',
            ),
            th.ParserTransfromRule(
                selector='div div div', mapping='forthResult',
            ),
            th.ParserTransfromRule(
                selector='div div div', mapping='fifthResult', attribute_name='attr'
            ),
            th.ParserTransfromRule(
                selector='.tc1', mapping='sixthResult',
                children=[
                    th.ParserTransfromRule(
                        selector='div', mapping='attr1', attribute_name='attr'
                    ),
                    th.ParserTransfromRule(
                        selector='div', mapping='value1',
                    ),
                ]
            ),
            th.ParserTransfromRule(
                selector='div[attr="1"]', mapping='seventhResult', regex_sub_value=['[^\d+]', ''],
            ),
            th.ParserTransfromRule(
                selector='h1', mapping='not_found',
            ),
        ]
        self.resultDict = json.loads(
            """{
            "attr1": [
                "1",
                "2"
            ],
            "fifthResult": [
                "1",
                "2"
            ],
            "firstResult": "CheckedText 1\\n                    \\n\\n                        CheckedText 2",
            "forthResult": [
                "CheckedText 1",
                "CheckedText 2"
            ],
            "secondResult": "CheckedText 1",
            "seventhResult": "1",
            "sixthResult": "CheckedText 1\\n                    \\n\\n                        CheckedText 2",
            "checked": [
                {
                "thridResult": "CheckedText 1"
                },
                {
                "thridResult": "CheckedText 2"
                }
            ],
            "checked2": [
                {"checked2": "CheckedText 1"},
                {"checked2": "CheckedText 2"}
            ],
            "value1": [
                "CheckedText 1",
                "CheckedText 2"
            ]
            }""")
        self.resultList = json.loads(
            """[
            "CheckedText 1\\n                    \\n\\n                        CheckedText 2",
            "CheckedText 1",
            {
                "checked": [
                {
                    "thridResult": "CheckedText 1"
                },
                {
                    "thridResult": "CheckedText 2"
                }
                ]
            },
            {
                "checked2": [
                {
                    "checked2": "CheckedText 1"
                },
                {
                    "checked2": "CheckedText 2"
                }
                ]
            },
            "CheckedText 1",
            "CheckedText 2",
            "1",
            "2",
            "CheckedText 1\\n                    \\n\\n                        CheckedText 2",
            "1",
            "2",
            "CheckedText 1",
            "CheckedText 2",
            "1"
            ]""")
    

    def test_basic(self):
        soup = BeautifulSoup("""
            <div>
                <div class="tc1">
                    <div attr="1">
                        CheckedText 1
                    </div>
                    <div attr="2">
                        CheckedText 2
                    </div>
                </div>
            </div>
        """, features="html.parser")
        
        data = {}
        th.transform_html(data, soup, self.rule,)
        self.assertDictEqual(
            data,
            self.resultDict, 
        )

        
        
        try:
            th.transform_html({}, soup, {
                'selector': 'h1', 'exception_on_not_found': True,
            })
        except LookupError as err:
            self.assertEqual(str(err), 'None found at all by selector "h1"')

    def test_list(self):
        soup = BeautifulSoup("""
            <div>
                <div class="tc1">
                    <div attr="1">
                        CheckedText 1
                    </div>
                    <div attr="2">
                        CheckedText 2
                    </div>
                </div>
            </div>
        """, features="html.parser")
        list_data = []
        th.transform_html(list_data, soup, self.rule,)
        self.assertEqual(
            list_data,
            self.resultList,
        )

    def test_bayut(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        html = open(f'{dir_path}/test_data/bayut_details.html', 'r').read()
        
        data = {}
        th.transform_html(data, html, [{
            'selector' : 'div[aria-label="Select country"] button',
            'mapping': 'Country'
        },
        {
            'selector' : 'div[aria-label="Property header"]',
            'children': [{
                'mapping': 'Title'
            },{
                'mapping': 'Address'
            }, {
                'mapping': 'City',
                'regex_sub_value': [r'(.*?, ?)([\w ]+)$', r'\2']
            }],
        },
        {
            'selector': '._5ffe039f', 
            'mapping': 'Features',
            
        }
        ],)
        logging.info(data)

        self.assertDictEqual(
            data,{
                'Country': 'UAE', 
                'City': 'Dubai',
                'Title': 'Dubai Marina Moon Tower, Dubai Marina, Dubai', 'Address': 'Dubai Marina Moon Tower, Dubai Marina, Dubai'}
        )

    def test_property_finder(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        html = open(f'{dir_path}/test_data/property_finder_list.html', 'r').read()
        rules = yaml.load(
            open(f'{dir_path}/test_data/property_finder_rules.yaml', 'r').read(),
            yaml.Loader
        )
        

        data = {}
        th.transform_html(data, html, rules)
        
        self.assertDictEqual(
            {'url': '/en/plp/buy/townhouse-for-sale-dubai-tilal-al-ghaf-aura-9415842.html', 'Source Link': 'https://www.propertyfinder.ae/en/plp/buy/townhouse-for-sale-dubai-tilal-al-ghaf-aura-9415842.html', 'ID': '9415842', 'Address': 'Aura, Tilal Al Ghaf, Dubai'},
            data['menu_items'][0],

        )


        



if __name__ == '__main__':
    unittest.main(verbosity=2)



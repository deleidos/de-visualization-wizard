__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"

import sys
import numpy
from copy import deepcopy
import requests

import logging
log = logging.getLogger(__name__)

from .visualization import Visualization

VALS_LIST = ['few', 'medium', 'many', 'infinite']

class DataMatcher:
    def __init__(self, modelerlocation):
        r = requests.get(modelerlocation + '/getschemas')
        data = r.json()
        r = requests.get(modelerlocation + '/getencodings')
        self.encodings = r.json()
        r = requests.get(modelerlocation + '/getarchetypes')
        self.archetypes = r.json()
        r = requests.get(modelerlocation + '/getdatasets')
        self.data_sets = r.json()
        r = requests.get(modelerlocation + '/getvisualizations')
        self.viz_array = [Visualization(viz, self.archetypes) for viz in r.json()]

        # associate each data set object with it's corresponding data object based on schema id
        for data_set in self.data_sets:
            for datum in data:
                if data_set['schema_ID'] == datum['sId']:
                    data_set['data'] = datum['sProfile']

    def dataSetRanking(self, domain, analytic_type, interpretation):
        data_set_scores = {}
        for data_set in self.data_sets:
            # domain (100's)
            if data_set['domain'] == domain:
                score = 100
            else:
                score = 0

            # analytic type (10's)
            if data_set['analytic_type'] == analytic_type:
                score += 10

            # interpretation (1's)
            for data_field in data_set['data']:
                if data_field['interpretation'] == interpretation:
                    score += 1
                    break

            # number of fields (decimal place)
            score += len(data_set['data']) * 0.0000001

            data_set_scores[data_set['name']] = score

        return data_set_scores

    def vizRanking(self, question_analysis):
        if 'rankUp' in question_analysis:
            rankUp = [t.lower() for t in question_analysis['rankUp']]
        else:
            rankUp = []

        if 'rankDown' in question_analysis:
            rankDown = [t.lower() for t in question_analysis['rankDown']]
        else:
            rankDown = []

        data_viz_ranks = []
        for data_set in self.data_sets:
            viz_ranks = []
            encoding_scores = self.matchEncodings(data_set['data'])
            archetype_scores = self.matchArchetypes(encoding_scores)

            for viz in self.viz_array:
                rank = viz.rank(data_set, archetype_scores, rankUp, rankDown)
                viz_dict = deepcopy(viz.__dict__)
                viz_dict.update(score=rank)
                viz_ranks.append(viz_dict)

            data_viz_ranks.append(dict({'name': data_set['name'], 'data': data_set, 'viz_ranks': viz_ranks}))

        return data_viz_ranks


    def matchEncodings(self, data_set):
        distinct_vals_list = [datum['numberDistinctValues'] for datum in data_set]
        FEW_THRESHOLD = min(15, numpy.percentile(distinct_vals_list, 15))
        MEDIUM_THRESHOLD = numpy.percentile(distinct_vals_list, 50)
        MANY_THRESHOLD = numpy.percentile(distinct_vals_list, 75)

        encoding_match_up = {}
        encoding_scores = {encoding['name']:[] for encoding in self.encodings}
        for field in data_set:
            attrs = field['attributes']
            fullName = field['fullName']
            numVals = field['numberDistinctValues']

            if numVals <= FEW_THRESHOLD:
                vals = 'few'
            elif numVals <= MEDIUM_THRESHOLD:
                vals = 'medium'
            elif numVals <= MANY_THRESHOLD:
                vals = 'many'
            else:
                vals = 'infinite'

            encoding_list = [encoding for encoding in self.encodings if self.attrMatch(attrs, encoding)]
            group_list = sorted(set(encoding['group'] for encoding in encoding_list))

            encoding_match_up[fullName] = []
            for encoding in encoding_list:
                step_score = 1
                enc_val = VALS_LIST.index(encoding['values'])
                data_val = VALS_LIST.index(vals)
                if enc_val > data_val:
                    step_score -= (enc_val - data_val) * 0.25
                elif enc_val < data_val:
                    step_score -= (data_val - enc_val) * 0.1

                group_score = 1 - (0.2 * group_list.index(encoding['group']))
                if (attrs['quantitative'] and encoding['name'] == 'position'):
                    group_score = 1

                encoding_score = step_score * group_score
                encoding_scores[encoding['name']].append(encoding_score)
                encoding_match_up[fullName].append((encoding['name'], encoding_score))

        return encoding_scores

    def matchArchetypes(self, encoding_scores):
        archetype_scores = {}
        for t in self.archetypes:
            max_vals = []
            for encoding, value in t['encodings'].items():
                if value > 0:
                    max_vals.append(0 if len(encoding_scores[encoding]) == 0 else max(encoding_scores[encoding]))

            archetype_score = sum(max_vals) / len(max_vals)
            archetype_scores[t['name']] = archetype_score

        return archetype_scores

    def attrMatch(s, attrs, encoding):
        return (attrs['identifier'] and encoding['identifier'] or
               attrs['categorical'] and encoding['categorical'] or
               attrs['quantitative'] and encoding['quantitative'] or
               attrs['relational'] and encoding['relational'] or
               attrs['ordinal'] and encoding['ordinal'])

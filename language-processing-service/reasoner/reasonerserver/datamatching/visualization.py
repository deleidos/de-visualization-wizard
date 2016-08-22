__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"

import requests

class Visualization:
    def __init__(self, vizdict, archetype_data):
        self.name = vizdict['name']
        self.analytic_type = vizdict['analytic_type']
        self.domains = vizdict['domains']
        self.interpretations = vizdict['mandatory_interpretations']
        self.thumbnail = vizdict['thumbnail']
        self.link = vizdict['link']

        self.archetypes = {archetype['name']:archetype for archetype in archetype_data if archetype['name'] in vizdict['archetypes']}
        self.viz_classifications = []
        for name, archetype in self.archetypes.items():
            self.viz_classifications += archetype['visual_classifications']

    def rank(self, data_set, archetype_scores, rankUp, rankDown):
        """Rank this viz against a given data set"""
        rank = 0

        # analytic type (1,000,000's)
        if self.analytic_type.lower() == data_set['analytic_type'].lower():
            rank += 1000000

        # domain (100,000's)
        if data_set['domain'] in self.domains:
            rank += 100000

        # wh term matching (10,000's, takes 4 digits)
        # does not consider the order of multiple archetypes when creating
        # the final classification list; may produce slightly skewed results
        rank += 7500
        for index, viztype in enumerate(self.viz_classifications):
            rankFactor = 5 - index
            if viztype.lower() in rankUp:
                rankUpIndex = rankUp.index(viztype.lower()) + 1
                rank += round(rankFactor * (1.0 / rankUpIndex), 1) * 1000
            elif viztype.lower() in rankDown:
                rankDownIndex = rankDown.index(viztype.lower()) + 1
                rank -= round(rankFactor * (1.0 / rankDownIndex), 1) * 1000

        # interpretations (1's)
        data_interpretations = list(set(data_field['interpretation'].lower() for data_field in data_set['data']))
        interp_match = True
        if len(self.interpretations) > 0:
            for interpretation in self.interpretations:
                if interpretation.lower() not in data_interpretations:
                        interp_match = False
                        break

            rank += 1 if interp_match else 0

        # encodings (decimal places)
        matching_archetypes = [score for archetype, score in archetype_scores.items() if archetype in self.archetypes]
        archetype_score_avg = sum(matching_archetypes) / len(matching_archetypes)
        rank += archetype_score_avg

        return rank

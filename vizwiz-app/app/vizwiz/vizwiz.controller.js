(function () {

    angular.module('vizwiz')
        .controller('VizwizController', VizwizController)
        .controller('VizResultsController', VizResultsController);

    VizwizController.$inject = [
        '$scope',
        '$location',
        '$state',
        '$log',
        '$window',
        '$uibModal',
        '$q',
        'questionAnalysisService',
        'word2vecService',
        'topicMatchingService',
        'dataSetService',
        'colorService',
        'modelerService'
    ];
    function VizwizController($scope, $location, $state, $log, $window, $uibModal, $q, questionAnalysisService,
                              word2vecService, topicMatchingService, dataSetService, colorService,
                              modelerService) {
        init();

        /**
            The following flag changes the word2vec method
            If *true*, then word2vec will group all question words and process against the domain
            If *false*, then word2vec will process each question word individually
         **/
        var groupWordVec = true;

        // Store all of the form data in this object
        $scope.formData = {};
        $scope.questionAnalysis = null;
        $scope.vizArray = [];
        $scope.topicScores = [];
        $scope.selectedTopic = null;

        $scope.count = 1;
        $scope.isThinking = false;
        $scope.kmSelected = false;
        $scope.showKM = false;
        $scope.showRestart = false;


        $scope.selectedViz = null;
        $scope.selectedDataSet = null;

        // These flags keep track of which parts of the form need to be disabled
        $scope.disableSpecifics = true;
        $scope.disableSeedValue = true;
        $scope.disableDataSet = true;
        $scope.disableResults = true;

        $scope.$location = $location;

        // Function to process the form
        $scope.processQuestion = processQuestion;
        $scope.selectTopic = selectTopic;
        $scope.setType = setType;
        $scope.correctQuestion = correctQuestion;
        $scope.selectDomain = selectDomain;
        $scope.dataSetRanking = dataSetRanking;
        $scope.pickViz = pickViz;
        $scope.startOver = startOver;


        //Functions that are bound to scope
        function processQuestion() {
            $scope.isThinking = true;
            $scope.kmSelected = false;
            $scope.topicScores = [];
            delete $scope.errorMessage;
            delete $scope.warningMessage;

            return analyzeQuestion($scope.formData.question)
                .then(findSimilarWords)
                .then(topicMatching)
                .finally(function () {
                    $scope.isThinking = false;
                });
        }

        function dataSetRanking() {
            var atype = $scope.questionAnalysis != null ? $scope.questionAnalysis.analyticType : "None";
            dataSetService.getDataSetRanking($scope.formData.domain, atype, $scope.formData.interpretation)
                .then(function (ranking) {
                    $scope.showRestart = true;
                    $scope.dataVizRanks.forEach(function (dataSet) {
                        dataSet.score = ranking[dataSet.name];
                    });
                    $scope.disableResults = false;
                    $state.go('vizwiz.results');
                    $log.log($scope.dataVizRanks);
                }, function (faultData) {
                    $scope.errorMessage = faultData.data.message;
                });
        }

        function selectTopic(topic) {
            $scope.selectedTopic = topic;
            $scope.formData.type = null;
            $scope.formData.seed = null;
            $scope.disableResults = true;

            searchKMTree($scope.treeNodes, topic);

            $scope.showKM = false;
            dataSetService.getVizRanking($scope.questionAnalysis).then(function (ranking) {
                $scope.dataVizRanks = ranking;

                var next;
                if ($scope.followUpQuestion) {
                    next = 'vizwiz.follow-up';
                    $scope.disableSpecifics = false;
                    $scope.disableSeedValue = true;
                } else {
                    next = 'vizwiz.data-sets';
                    $scope.disableSeedValue = false;
                }

                $state.go(next);
            }, function (faultData) {
                $scope.errorMessage = faultData.data.message;
            });
        }

        function setType(type) {
            $scope.formData.seed = null;
            $scope.formData.type = type;
            $state.go('vizwiz.data-sets');
            $scope.disableSeedValue = false;
        }

        function correctQuestion() {
            $scope.formData.question = $scope.questionAnalysis.correctedQuestion;
            delete $scope.questionAnalysis.correctedQuestion;
        }

        function selectDomain(domain) {
            $scope.showKM = true;
            modelerService.getTaxonomy(domain).then(function (knowledgeModel) {
                delete $scope.errorMessage;
                $scope.treeNodes = knowledgeModel.taxonomy;
            }, function (faultData) {
                delete $scope.treeNodes;
                $scope.errorMessage = faultData.data.message + " Visualization wizard cannot process without a taxonomy";
            });
        }

        function pickViz(viz, dataSet) {
            var modalInstance = $uibModal.open({
                templateUrl: 'more-details.html',
                controller: 'VizResultsController',
                size: 'lg',
                resolve: {
                    viz: function () {
                        return viz;
                    },
                    dataSet: function () {
                        return dataSet;
                    }
                }
            });

            modalInstance.result.then(function (selectedViz) {
                $window.open(selectedViz.link, '_blank');
            }, function () {
            });
        }

        function startOver() {
            $state.go('vizwiz.question', {}, {reload: true});
        }

        // Other functions
        function init() {
            $q.all({
                domainsResult: modelerService.getDomains(),
                interpsResult: modelerService.getInterpretations()
            }).then(function (successData) {
                $scope.domains = successData.domainsResult;
                $scope.interpretations = successData.interpsResult;
            }, function (faultData) {
                $scope.errorMessage = "The domains and/or interpretations could not be found. Make sure the reasoner and " +
                    "modeler servers are running and accessible and try again.";

                $log.error(faultData);
            });
        }

        function searchKMTree(taxonomy, topic) {
            taxonomy.forEach(function (node) {
                if (node.children && node.children.length > 0) {
                    searchKMTree(node.children, topic);
                } else {
                    if (node.name.toLowerCase() === topic.toLowerCase()) {
                        if (node.subquestion && node.subanswers) {
                            $scope.followUpQuestion = node.subquestion;
                            $scope.followUpAnswers = node.subanswers;
                        }
                    }
                }
            });
        }

        function analyzeQuestion(question) {
            return questionAnalysisService.analyze(question)
                .then(function (qa) {
                    $log.log(qa);
                    $scope.questionAnalysis = qa;

                    if (qa.correctedWords.length > 0) {
                        $scope.questionAnalysis.correctedQuestion = qa.question;
                        qa.correctedWords.forEach(function (word) {
                            $scope.questionAnalysis.correctedQuestion = $scope.questionAnalysis.correctedQuestion.replace(word.orig, word.corrected);
                        });
                    }

                    return qa;
                });
        }

        function findSimilarWords(qa) {
            var nouns = [];
            // Extract the nouns to run word2vec against
            qa.tagged.forEach(function (taggedWord) {
                if (taggedWord[1].indexOf('NN') > -1) {
                    nouns.push(taggedWord[0]);
                }
            });

            var promise;
            if (groupWordVec) {
                promise = word2vecService.wordvecGroup(nouns, $scope.formData.domain);
            } else {
                promise = word2vecService.wordvecLoop(nouns, $scope.formData.domain);
            }

            return promise.then(function (similarWordsData) {
                var ngrams = qa.bigrams.concat(qa.trigrams);
                return [similarWordsData, ngrams, qa.lemmas];
            }, function (faultData) {
                $log.error(faultData);
                $scope.warningMessage = faultData.data.message + "Visualization Wizard can" +
                    " still function but may result in weaker matches.";
                var ngrams = qa.bigrams.concat(qa.trigrams);
                return [[], ngrams, qa.lemmas];
            });
        }

        function topicMatching(data) {
            return topicMatchingService.processQuestion($scope.formData.question, data[0], data[1], data[2], $scope.formData.domain)
                .then(function (successData) {
                    $scope.topicScores = successData.data;

                    $scope.topicScores.forEach(function (ts) {
                        if (ts.score >= 0.7) {
                            ts.strength = 2;
                            ts.msg = 'This is a strong result';
                        } else if (ts.score < 0.7 && ts.score >= 0.5) {
                            ts.strength = 1;
                            ts.msg = 'This is a moderate result';
                        } else {
                            ts.strength = 0;
                            ts.msg = 'This is a weak result';
                        }

                        // TODO: Decide on continuous colors based on score vs three discrete colors
                        // See color service in common
                        var rgb = colorService.getColor(ts.score);
                        ts.color = { color: rgb };
                    });

                    return successData.data;
                }, function (faultData) {
                    $scope.errorMessage = faultData.data.message;
                });
        }

        /* watchers */
        $scope.$on('selection-changed', function (e, node) {
            //node - selected node in tree
            if (!node.children || !node.children.length) {
                $scope.warningMessage = "A topic has been selected without asking a question. Visualization Wizard can" +
                    " still function but will not have question analytic data and may result in weaker matches.";
                $scope.selectedNode = node;
                $scope.kmSelected = true;
            }
        });

        $scope.$on('expanded-state-changed', function (e, node) {
            // node - the node on which the expanded state changed
            // to see the current state check the expanded property
            //$log.log(node.expanded);
            $scope.exapndedNode = node;
        });

    }

    VizResultsController.$inject = ['$scope', '$uibModalInstance', 'viz', 'dataSet'];
    function VizResultsController($scope, $uibModalInstance, viz, dataSet) {
        $scope.viz = viz;
        $scope.dataSet = dataSet;

        $scope.select = function () {
            $uibModalInstance.close($scope.viz);
        };

        $scope.cancel = function () {
            $uibModalInstance.dismiss('cancel');
        };
    }
})();

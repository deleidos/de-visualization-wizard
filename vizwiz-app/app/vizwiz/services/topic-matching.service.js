(function () {
    "use strict";

    angular.module('vizwiz')
        .factory('topicMatchingService', wordMatchingService);

    wordMatchingService.$inject = ['$http', '$q', '$rootScope'];
    function wordMatchingService($http, $q, $rootScope) {
        return {
            processQuestion: processQuestion
        };

        function processQuestion(question, similarWords, ngrams, lemmas, domain) {
            var deferred = $q.defer();

            var qwords = {};
            if (question) {
                question.split(' ').forEach(function (word) {
                    qwords[word] = 1.0;
                });
            }

            // group
            if (similarWords && similarWords.result &&
                similarWords.result.most_similar_terms && similarWords.result.most_similar_terms.length > 0) {
                similarWords.result.most_similar_terms.forEach(function (wordObj) {
                    qwords[wordObj[0]] = wordObj[1];
                });
            }

            // loop
            if (similarWords && similarWords.length) {
                similarWords.forEach(function (res) {
                    res.result.most_similar_terms.forEach(function (wordObj) {
                        qwords[wordObj[0]] = wordObj[1];
                    });
                });
            }

            if (ngrams && ngrams.length > 0) {
                ngrams.forEach(function (ngram) {
                    qwords[ngram] = 1.0;
                });
            }

            if (lemmas && lemmas.length > 0) {
                lemmas.forEach(function (lemma) {
                    qwords[lemma] = 1.0;
                });
            }

            $http.get($rootScope.reasonerUrl + 'topicmatching/' + domain, {
                    params: qwords,
                    headers: {
                        'Content-Type':'text/plain'
                }
            }).then(function (successRespons) {
                deferred.resolve(successRespons);
            }, function (failureResponse) {
                deferred.reject(failureResponse);
            });

            return deferred.promise;
        }
    }
})();

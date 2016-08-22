(function () {
    "use strict";

    angular.module('vizwiz')
        .factory('word2vecService', w2vService);

    w2vService.$inject = ['$q', '$http', '$rootScope'];
    function w2vService($q, $http, $rootScope) {
        return {
            wordvec: wordvec,
            wordvecGroup: wordvecGroup,
            wordvecLoop: wordvecLoop
        };

        function wordvec(domain, word) {
            var deferred = $q.defer();

            $http.get($rootScope.modelerUrl + 'processmodel/' + domain + '/' + word.split(' ').join('&'), {
                headers: {
                    'Content-Type':'application/json'
                }
            }).then(function (successResponse) {
                deferred.resolve({word: word, result: successResponse.data});
            }, function(failureResponse) {
                deferred.reject(failureResponse);
            });

            return deferred.promise;
        }

        function wordvecGroup(nouns, domain) {
            var deferred = $q.defer();

            nouns.push(domain);
            var checkword = nouns.map(function(word) { return word.toLowerCase(); }).join(' ');
            var promise = wordvec(domain, checkword);
            promise.then(function (successResponse) {
                deferred.resolve(successResponse);
            }, function(failureResponse) {
                deferred.reject(failureResponse);
            });

            return deferred.promise;
        }

        function wordvecLoop(nouns, domain) {
            var deferred = $q.defer();

            var promises = [];
            nouns.forEach(function (word) {
                var checkword = domain.toLowerCase() + ' ' + word.toLowerCase();
                promises.push(wordvec(domain, checkword));
            });

            $q.all(promises).then(function (successResponse) {
                deferred.resolve(successResponse);
            }, function (failureResponse) {
                deferred.reject(failureResponse);
            });

            return deferred.promise;
        }
    }

})();

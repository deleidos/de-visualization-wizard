(function () {
    "use strict";

    angular.module('vizwiz')
        .factory('questionAnalysisService', qaService);

    qaService.$inject = ['$q', '$http', '$rootScope'];
    function qaService($q, $http, $rootScope) {
        return {
            analyze: analyze
        };

        function analyze(question) {
            var deferred = $q.defer();

            $http.get($rootScope.reasonerUrl + 'questionanalysis/' + question, {
                headers: {
                    'Content-Type':'application/json'
                }
            }).then(function (successResponse) {
                deferred.resolve(angular.extend(successResponse.data, { question: question }));
            }, function(failureResponse) {
                deferred.reject(failureResponse);
            });

            return deferred.promise;
        }
    }
})();

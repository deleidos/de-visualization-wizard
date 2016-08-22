(function () {
    "use strict";

    angular.module('vizwiz')
        .factory('dataSetService', dataSetService);

    dataSetService.$inject = ['$q', '$http', '$rootScope'];
    function dataSetService($q, $http, $rootScope) {
        return {
            getDataSetRanking: getDataSetRanking,
            getVizRanking: getVizRanking
        };

        function getDataSetRanking(domain, analyticType, interpretation) {
            var deferred = $q.defer();

            $http.get($rootScope.reasonerUrl + 'datasetranking/' + domain + '/' + analyticType + '/' + interpretation, {
                headers: {
                    'Content-Type': 'application/json'
                }
            }).then(function (successResponse) {
                deferred.resolve(successResponse.data);
            }, function (failureResponse) {
                deferred.reject(failureResponse);
            });

            return deferred.promise;
        }

        function getVizRanking(questionAnalysis) {
            var deferred = $q.defer();

            $http.get($rootScope.reasonerUrl + 'vizranking', {
                params: questionAnalysis,
                headers: {
                    'Content-Type': 'application/json'
                }
            }).then(function (successResponse) {
                deferred.resolve(successResponse.data);
            }, function (failureResponse) {
                deferred.reject(failureResponse);
            });

            return deferred.promise;
        }
    }
})();

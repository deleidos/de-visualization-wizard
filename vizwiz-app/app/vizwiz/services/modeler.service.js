(function () {
    "use strict";

    angular.module('vizwiz')
        .factory('modelerService', modelerService);

    modelerService.$inject = ['$q', '$http', '$rootScope'];
    function modelerService($q, $http, $rootScope) {
        return {
            getTaxonomy: getTaxonomy,
            getDomains: getDomains,
            getInterpretations: getInterpretations
        };

        function getTaxonomy(domain) {
            var deferred = $q.defer();

            $http.get($rootScope.modelerUrl + 'gettaxonomyfordomain/' + domain, {
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

        function getDomains() {
            var deferred = $q.defer();

            $http.get($rootScope.modelerUrl + 'getdomains', {
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

        function getInterpretations() {
            var deferred = $q.defer();

            $http.get($rootScope.modelerUrl + 'getinterpretations', {
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

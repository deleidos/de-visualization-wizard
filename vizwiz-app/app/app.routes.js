(function () {
    "use strict";

    angular.module('vizwiz')
        .config(routeConfig);

    routeConfig.$inject = ['$stateProvider', '$urlRouterProvider'];
    function routeConfig($stateProvider, $urlRouterProvider) {
        $stateProvider
            .state('vizwiz', {
                url: '/',
                templateUrl: 'vizwiz/partials/form.html',
                controller: 'VizwizController'
            })
            .state('vizwiz.question', {
                url: 'question',
                templateUrl: 'vizwiz/partials/question.html'
            })
            .state('vizwiz.follow-up', {
                url: 'follow-up',
                templateUrl: 'vizwiz/partials/follow-up.html'
            })
            .state('vizwiz.data-sets', {
                url: 'data-sets',
                templateUrl: 'vizwiz/partials/data-sets.html'
            })
            .state('vizwiz.results', {
                url: 'results',
                templateUrl: 'vizwiz/partials/results.html'
            });
        $urlRouterProvider.otherwise('/');
    }
})();

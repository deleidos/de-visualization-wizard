(function () {
    "use strict";

    angular.module('vizwiz', [
        'ui.router',
        'ui.bootstrap',
        'ngAnimate',
        'TreeWidget',
        'RecursionHelper'
    ])
    .run(['$rootScope', '$location', '$state', function($rootScope, $location, $state) {
        $rootScope.reasonerUrl = '';
        $rootScope.modelerUrl = '';

        // on a refresh go back to the home page
        $rootScope.$on('$locationChangeStart', function (event, next, curr) {
            if (next === curr) {
                event.preventDefault();
                $state.go('vizwiz');
            }
        });

    }]);
})();

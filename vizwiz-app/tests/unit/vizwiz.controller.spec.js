describe('VizwizController', function () {
    var testScope;
    var $state;
    var $location;

    beforeEach(function () {
        module('vizwiz');
        inject(function ($controller, $rootScope, _$state_, _$location_) {
            testScope = $rootScope.$new();
            $state = _$state_;
            $location = _$location_;
            $controller('VizwizController', {
                $scope: testScope,
                $state: _$state_
            });
        });
    });

    it('should successfully initiate data', function () {
        expect(testScope.formData).toEqual({});
        expect(testScope.questionAnalysis).toBeNull();
        expect(testScope.vizArray.length).toBe(0);
        expect(testScope.topicScores.length).toBe(0);
        expect(testScope.selectedTopic).toBeNull();

        expect(testScope.count).toBe(1);
        expect(testScope.isThinking).toBe(false);
        expect(testScope.kmSelected).toBe(false);

        expect(testScope.disableSpecifics).toBe(true);
        expect(testScope.disableSeedValue).toBe(true);
        expect(testScope.disableDataSet).toBe(true);
    });

    it('should process a question without failing', function () {
        testScope.formData.question = 'Where will my target sleep tonight?';
        var promise = testScope.processQuestion();
        promise.then(function () {
            expect(testScope.isThinking).toBe(false);
        });
    });

    xdescribe('the selectTopic function', function () {
        it('should select a topic', function () {
            var testTopic = 'test';
            testScope.selectTopic(testTopic);
            expect(testScope.selectedTopic).toBe(testTopic);
        });

        it('should make type and seed null', function () {
            testScope.selectTopic('blah');
            expect(testScope.formData.type).toBeNull();
            expect(testScope.formData.seed).toBeNull();
        });

        it('should disable the correct pages', function () {
            testScope.selectTopic('Bed down');
            expect(testScope.disableSpecifics).toBe(false);
            expect(testScope.disableSeedValue).toBe(true);

            testScope.selectTopic('Home range');
            expect(testScope.disableSeedValue).toBe(false);
        });
    });

    describe('the setType function', function () {
        it('should set the type', function () {
            var testType = 'test';
            testScope.setType(testType);
            expect(testScope.formData.type).toBe(testType);
        });

        it('should make seed null', function () {
            testScope.setType('blah');
            expect(testScope.formData.seed).toBeNull();
        });

        it('should disable the correct pages', function () {
            testScope.setType('blah');
            expect(testScope.disableSeedValue).toBe(false);
        });
    });
});

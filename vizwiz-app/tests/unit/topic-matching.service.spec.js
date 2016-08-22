describe('topicMatchingService', function () {
    var topicMatchingService;
    var $httpBackend;
    var $rootScope;

    beforeEach(function () {
        module('vizwiz');
        inject(function (_topicMatchingService_, _$httpBackend_, _$rootScope_) {
            topicMatchingService = _topicMatchingService_;
            $httpBackend = _$httpBackend_;
            $rootScope = _$rootScope_;

            $httpBackend.whenGET(/.*\.html$/).respond(200, '');
        });
    });

    it('should have a processQuestion function', function () {
        expect(topicMatchingService.processQuestion).toBeDefined();
        expect(angular.isFunction(topicMatchingService.processQuestion)).toBe(true);
    });

    describe('the processQuestion function', function () {
        it('should work with no arguments', function () {
            var promise = topicMatchingService.processQuestion();
            promise.then(function (data) {
                console.log(data);
                expect(data).toBeDefined();
            });
        });

        it('should work with empty arguments', function () {
            topicMatchingService.processQuestion('', {}, [], []);
        });

        it('should work with all arguments', function () {
            var question = 'What is a good test question to ask?';
            var similarWords = {
                result: {
                    most_similar_terms: [['blah', 0.4], ['abc', 0.5], ['xyz', 0.6]]
                }
            };

            var ngrams = ['What is', 'is a', 'a good', 'good test', 'test question', 'question to', 'to ask'];
            var lemmas = ['check'];
            var domain = 'National Security';

            // sorry about this
            $httpBackend.expectGET($rootScope.reasonerUrl + 'topicmatching/National Security?What=1&What+is=1&a=1&a+good=1&abc=0.5' +
                                             '&ask%3F=1&blah=0.4&check=1&good=1&good+test=1&is=1&is+a=1' +
                                             '&question=1&question+to=1&test=1&test+question=1&to=1&to+ask=1&xyz=0.6')
                .respond(200, '');

            topicMatchingService.processQuestion(question, similarWords, ngrams, lemmas, domain);
            $httpBackend.flush();

            $httpBackend.verifyNoOutstandingExpectation();
            $httpBackend.verifyNoOutstandingRequest();
        });
    });

});

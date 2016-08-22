describe('word2vecService', function () {
    var word2vecService;

    beforeEach(function () {
        module('vizwiz');
        inject(function (_word2vecService_) {
            word2vecService = _word2vecService_;
        });
    });

    it('should have a group function', function () {
        expect(word2vecService.wordvecGroup).toBeDefined();
        expect(angular.isFunction(word2vecService.wordvecGroup)).toBe(true);
    });

    it('should have a loop function', function () {
        expect(word2vecService.wordvecLoop).toBeDefined();
        expect(angular.isFunction(word2vecService.wordvecLoop)).toBe(true);
    });
});

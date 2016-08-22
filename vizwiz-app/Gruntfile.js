/*global module:false*/
module.exports = function (grunt) {

    require('jit-grunt')(grunt, {
        useminPrepare: 'grunt-usemin'
    });
    require('time-grunt')(grunt);

    // Project configuration.
    grunt.initConfig({
        // Metadata
        pkg: grunt.file.readJSON('package.json'),
        banner: '/*! <%= pkg.title || pkg.name %> - v<%= pkg.version %> - ' +
        '<%= grunt.template.today("yyyy-mm-dd") %> */\n',
        meta: {
            app_files: ['app/**/*.js', '!app/bower_components/**/*', '!app/assets/lib/**/*'],
            lib_files: ['app/assets/lib/**/*'],
            dist_dir: 'dist',
            temp_dir: '.tmp'
        },

        // Task configuration
        connect: {
            server: {
                options: {
                    port: 9000,
                    base: 'app',
                    open: true,
                    hostname: 'localhost',
                    livereload: !grunt.option('no-reload'),
                    keepalive: grunt.option('no-reload')
                }
            },
            dist: {
                options: {
                    base: '<%= meta.dist_dir %>',
                    open: true
                }
            }
        },
        copy: {
            dist: {
                files: [{
                    expand: true,
                    dot: true,
                    cwd: 'app',
                    dest: '<%= meta.dist_dir %>',
                    filter: 'isFile',
                    src: [
                        '**/*',
                        '!**/*.js',
                        '!**/*.css',
                        '!bower_components/**/*',
                        '!assets/lib/**/*'
                    ]
                }, {
                    expand: true,
                    dot: true,
                    cwd: 'app/bower_components/bootstrap-css-only/fonts',
                    dest: '<%= meta.dist_dir %>/assets/fonts',
                    src: ['*']
                }, {
                    expand: true,
                    dot: true,
                    cwd: 'app/bower_components/font-awesome/fonts',
                    dest: '<%= meta.dist_dir %>/assets/fonts',
                    src: ['*']
                }, {
                    expand: true,
                    dot: true,
                    cwd: 'app/bower_components/angular-ui-grid',
                    dest: '<%= meta.dist_dir %>/assets/css',
                    src: ['*.woff', '*.ttf', '*.svg', '*.eot']
                }, {
                    expand: true,
                    dot: true,
                    cwd: 'app/assets/lib/angular-tree-widget-master/img',
                    dest: '<%= meta.dist_dir %>/assets/css/img',
                    src: ['*']
                }]
            }
        },
        clean: {
            dist: '<%= meta.dist_dir %>',
            temp: '<%= meta.temp_dir %>',
            coverage: 'coverage'
        },
        htmlmin: {
            dist: {
                options: {
                    collapseWhitespace: true,
                    collapseBooleanAttributes: true,
                    removeCommentsFromCDATA: true,
                    removeOptionalTags: true
                },
                files: [{
                    expand: true,
                    cwd: '<%= meta.dist_dir %>',
                    src: ['**/*.html'],
                    dest: '<%= meta.dist_dir %>'
                }]
            }
        },
        jshint: {
            options: {
                jshintrc: true
            },
            gruntfile: {
                src: 'Gruntfile.js'
            },
            app_files: {
                src: '<%= meta.app_files %>'
            }
        },
        jscs: {
            options: {
                config: '.jscsrc',
                fix: true
            },
            src: '<%= meta.app_files %>'
        },
        karma: {
            all: {
                configFile: 'karma.conf.js',
                singleRun: true
            },
            chrome: {
                configFile: 'karma.conf.js',
                singleRun: true,
                browsers: ['Chrome']
            },
            firefox: {
                configFile: 'karma.conf.js',
                singleRun: true,
                browsers: ['Firefox']
            },
            ie: {
                configFile: 'karma.conf.js',
                singleRun: true,
                browsers: ['IE']
            },
            phantomjs: {
                configFile: 'karma.conf.js',
                singleRun: true,
                browsers: ['PhantomJS']
            },
            watch: {
                configFile: 'karma.conf.js',
                singleRun: false,
                autoWatch: true,
                browsers: ['Chrome']
            }
        },
        ngAnnotate: {
            options: {
                singleQuotes: true
            },
            app_files: {
                files: [{
                    expand: true,
                    src: '<%= meta.temp_dir %>/concat/js/<%= pkg.name %>.js'
                }]
            }
        },
        postcss: {
            options: {
                map: true,
                failOnError: true,
                processors: [
                    require('pixrem')(),
                    require('autoprefixer')(),
                    require('cssnano')()
                ]
            },
            dist: {
                src: '<%= meta.temp_dir %>/concat/assets/css/<%= pkg.name %>.css',
                dest: '<%= meta.dist_dir %>/assets/css/<%= pkg.name %>.css'
            }
        },
        usemin: {
            html: '<%= meta.dist_dir %>/index.html'
        },
        useminPrepare: {
            html: 'app/index.html',
            options: {
                dest: '<%= meta.dist_dir %>',
                staging: '<%= meta.temp_dir %>'
            }
        },
        watch: {
            livereload: {
                files: ['<%= meta.app_files %>', 'app/**/*.html', 'app/**/*.css'],
                options: {
                    livereload: true
                }
            },
            gruntfile: {
                files: '<%= jshint.gruntfile.src %>',
                tasks: ['jshint:gruntfile']
            },
            jshint: {
                files: '<%= meta.app_files %>',
                tasks: ['newer:jshint:app_files', 'newer:jscs']
            }
        },
        wiredep: {
            app: {
                src: ['app/index.html']
            },
            test: {
                src: ['karma.conf.js'],
                devDependencies: true
            }
        }
    });

    grunt.registerTask('serve', function (target) {
        if (target === 'dist') {
            return grunt.task.run('connect:dist:keepalive');
        }

        grunt.task.run(['wiredep', 'connect:server']);
        if (!grunt.option('no-reload')) {
            grunt.task.run('watch:livereload');
        }
    });

    grunt.registerTask('test', function (target) {
        grunt.task.run(['clean:coverage', 'wiredep:test', 'karma:' + (target ? target : 'all')]);
    });

    grunt.registerTask('check-code', ['newer:jshint', 'newer:jscs']);

    grunt.registerTask('build', [
        'clean:dist',
        'wiredep:app',
        'useminPrepare',
        'concat',
        'ngAnnotate',
        'copy:dist',
        'cssmin',
        'postcss',
        'uglify',
        'usemin',
        'clean:temp'
    ]);

    grunt.registerTask('default', [
        'newer:jshint',
        'newer:jscs',
        'test:phantomjs',
        'build'
    ]);
};

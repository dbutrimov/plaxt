const gulp = require('gulp');
const del = require('del');

function bootstrap() {
    function bootstrap_clean(cb) {
        del.sync(['./static/bootstrap'])
        cb()
    }

    function bootstrap_css() {
        const files = [
            './node_modules/bootstrap/dist/css/*',
            '!./node_modules/bootstrap/dist/css/bootstrap.rtl*',
            '!./node_modules/bootstrap/dist/css/bootstrap-grid*',
            '!./node_modules/bootstrap/dist/css/bootstrap-reboot*',
            '!./node_modules/bootstrap/dist/css/bootstrap-utilities*',
        ]
        return gulp.src(files)
            .pipe(gulp.dest('./static/bootstrap/css'))
    }

    function bootstrap_javascript() {
        const files = [
            './node_modules/bootstrap/dist/js/*',
            '!./node_modules/bootstrap/dist/js/bootstrap.esm*',
        ]
        return gulp.src(files)
            .pipe(gulp.dest('./static/bootstrap/js'))
    }

    return gulp.series(bootstrap_clean, gulp.parallel(bootstrap_css, bootstrap_javascript))
}

function bootstrap_icons() {
    function bootstrap_icons_clean(cb) {
        del.sync(['./static/bootstrap-icons'])
        cb()
    }

    function bootstrap_icons_font() {
        const files = [
            './node_modules/bootstrap-icons/font/**',
            '!./node_modules/bootstrap-icons/font/index.html',
        ]
        return gulp.src(files)
            .pipe(gulp.dest('./static/bootstrap-icons/font'))
    }

    return gulp.series(bootstrap_icons_clean, gulp.parallel(bootstrap_icons_font))
}

function jquery() {
    function jquery_clean(cb) {
        del.sync(['./static/jquery'])
        cb()
    }

    function jquery_javascript() {
        const files = [
            './node_modules/jquery/dist/*',
            '!./node_modules/jquery/dist/jquery.slim*',
            '!./node_modules/jquery/dist/popper*',
        ]
        return gulp.src(files).pipe(gulp.dest('./static/jquery'))
    }

    return gulp.series(jquery_clean, gulp.parallel(jquery_javascript))
}

function moment() {
    function moment_clean(cb) {
        del.sync(['./static/moment'])
        cb()
    }

    function moment_javascript() {
        const files = [
            './node_modules/moment/min/moment.min.*',
        ]
        return gulp.src(files).pipe(gulp.dest('./static/moment'))
    }

    return gulp.series(moment_clean, gulp.parallel(moment_javascript))
}

exports.default = gulp.series(
    bootstrap(),
    bootstrap_icons(),
    jquery(),
    moment(),
)

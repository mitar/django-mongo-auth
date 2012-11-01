(function ($) {
    $(document).ready(function () {
        $('#browserid_submit').submit(function (event) {
            $(this).closest('form').submit();
        });
    });
})(jQuery);
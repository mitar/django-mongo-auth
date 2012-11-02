(function ($) {
    $(document).ready(function () {
        // When BrowserID returns, it calls submit on
        // browserid_submit, so we redirect it to the form
        $('#browserid_submit').submit(function (event) {
            event.preventDefault();
            $(this).closest('form').submit();
        });
    });
})(jQuery);
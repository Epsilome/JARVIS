(function($) {



})(jQuery);



jQuery(document).ready(function($) {

    //open block by link hash
if( $('.what_new_page').length ){
    if(window.location.hash) {
        window.scrollTo(0, 0);
        var url = window.location.href;
        var hash = window.location.hash.replace('#', '');
        //console.log(hash);
        setTimeout(function(){

            if ($(window).width() < 767) {
                var top_ofset = 100;
            } else if($(window).width() < 575) {
                var top_ofset = 40;
            } else{
                var top_ofset = 150;
            }

            var x = $('#'+hash).next().show();
            $('html,body').animate({
              scrollTop: $('#'+hash).offset().top - top_ofset
            }, 1700);

        }, 300);
    }

    setTimeout(function(){

        $.fn.isBefore= function(sel){
          return this.nextAll(sel).length !== 0;
        }

        if ($('.hide_content').length ) {
            //console.log('hide_content');
            var insert_before = $('.open_content');
            $('<div class="collapse_btn_block"><span class="expandAll">Expand all</span><span class="collapseAll">Collapse all</span></div>')
                .insertBefore( insert_before );
               // .insertBefore( $('.container .titles_show:first-child') );
        }

        $('.expandAll').on('click', function(){
            $( ".hide_content" ).show();
        });

        $('.collapseAll').on('click', function(){
            $( ".hide_content" ).hide();
        });

        if($('.collapse_btn_block').prevAll("h2").length ) {
            //$('.collapse_btn_block').addClass('h2_before');
            var collapse_block = $('.collapse_btn_block'); 
            var collapse_block_prev = $('.collapse_btn_block').prev(); 

            $(collapse_block_prev).prepend(collapse_block);  

            //$( collapse_block_prev ).replaceWith( collapse_block );
        }



    }, 100);
}


    if ($(window).width() > 767) {

        var pop_up = $('.ajax-popup');
        if(pop_up.length){
            $('head').append('<link rel="stylesheet" href="/source/css/magnific-popup.css" type="text/css">');
            $('head').append('<script src="/source/js/jquery.magnific-popup.min.js"></script>');

            pop_up.magnificPopup({
              type: 'image',
              mainClass: 'mfp-fade',
            });
        }

        var url = window.location.href;
        set_active_url(url);

        var num = 0; //number of pixels before modifying styles
        $(window).bind('scroll', function () {
            if ($(window).scrollTop() > num) {
                if($('body').hasClass('simpl_page')){
                    $('main').css('padding-top', "66px");
                }
            }
        });

        $("a[href^='#']").on('click', function(e) {
           // prevent default anchor click behavior
           e.preventDefault();
           // animate
           $('html, body').animate({
               scrollTop: $(this.hash).offset().top - 150
             }, 300, function(){
             });
        });

    }else{

        $(".product a[href^='#']").on('click', function(e) {
           // prevent default anchor click behavior
           e.preventDefault();
           // animate
           $('html, body').animate({
               scrollTop: $(this.hash).offset().top - 90
             }, 300, function(){
             });
        });

        //change place image after text
        $('.change_place').each( function(){
            var next = $(this).next();
            $(this).before(next);
            console.log('123');
        });

        //fixed product menu on product page
        if($( "body" ).hasClass( "product" )){
            var num = 49; //number of pixels before modifying styles
            $(window).bind('scroll', function () {
                if ($(window).scrollTop() > num) {
                    $('#prod_menu').addClass('fixed_prod_mobile');
                    if($(window).width() > 575){
                        $('main').css('padding-top', "90px");
                    }else{
                        $('main').css('padding-top', "83px");
                    }
                    
                    $('#main_menu button.navbar-toggler').addClass('fixed_button');
                    $('#navbarSupportedContent').addClass('fixed_dropdown_menu');
                } else {
                    $('#prod_menu').removeClass('fixed_prod_mobile');
                    $('main').css('padding-top', "0px");
                    $('#main_menu button.navbar-toggler').removeClass('fixed_button');
                    $('#navbarSupportedContent').removeClass('fixed_dropdown_menu');
                }
            });
        }

    }

    //select product version, change price
    $('.btn_select_version').on('click', function(){
        var price = $(this).attr('data-product-price');
        var desc_product = $(this).find('span').text();
        $('#price_value').text(price);
        $('#product_desc').text(desc_product);
        $('.btn_select_version.active').removeClass('active');
        $(this).addClass('active');

        if ($(window).width() < 767) {

            if($(this).hasClass('active')){
                $(this).siblings('.btn_select_version').toggle();
                
            }

            if($(this).index() != 0){
                //console.log('hello');
                $(this).siblings('.btn_select_version').not('.active').hide();
            }

            $(this).siblings('.btn_select_version').insertAfter($(this));

        }

    });
    
    //search field
    $('#search_form button').click(function(){
        var input = $(this).parent().find('input');
        if(input.hasClass('open')){
            if(input.val() != ''){
                return true;
            }else{
                input.removeClass('open');
                return false;      
            }
            
        }else{
            input.addClass('open');
            return false;
        }
        
    });

// mobile script

    if ($(window).width() < 767) {

        $('.collapse').collapse({
            toggle: false
          })

        $(".block_title_icon .title_info").siblings('.block_title_icon .title_icon').insertAfter($(".block_title_icon .title_info"));

        //change places copyright block in mobile version
        $( "#footer_copyright_block .row" ).prepend( $( "#paiment_types" ) );

        $('#tabs_block .show').removeClass("show");

        //top slider on mobile version
        var mobile_slider_nav = $('#mobile_slider_nav');
        var gallery_imgs = $('.img_prew img');
        var first_img_in_slider = $('.block_title_icon .wrapp_title_icon img');
        var slider_nav_elements = '<div data-img-src="'+ first_img_in_slider.attr( 'src' ) +'" class="dot_nav active"></div>';
        gallery_imgs.each(function( index ) {
            
            slider_nav_elements += '<div data-img-src="'+ $( this ).attr( 'src' ) +'" class="dot_nav"></div>';
        });
        mobile_slider_nav.prepend(slider_nav_elements);

        // change image in mobile gallery
        $('#mobile_slider_nav .dot_nav').on('click', function(){
            
            var url = $(this).attr( "data-img-src" );
            var big_img = $(this).closest('.title_icon').find('.wrapp_title_icon');
            big_img.find('img').fadeOut('slow').remove();
            big_img.prepend("<img src="+url+" />");
            $(this).closest('.title_icon').find('.dot_nav.active').removeClass('active');
            $(this).addClass('active');
            
        }); 

        $( ".block_title_icon .wrapp_title_icon" ).append("<div class='left_slide mobile_on_img_slide'></div><div class='right_slide mobile_on_img_slide'></div>");

        $( ".block_title_icon .right_slide" ).on('click', function(){
            var block_gallery = $(this).closest('.title_icon');
            var active_url = block_gallery.find('.dot_nav.active');
            var next_url = active_url.next();
            if( next_url.length == 0 ) {
               next_url = block_gallery.find('.dot_nav').first();
            }        
            var big_img = block_gallery.find('.wrapp_title_icon');
    
            big_img.find('img').fadeOut('slow').remove();
            big_img.prepend("<img src="+next_url.attr( "data-img-src" )+" />");
            active_url.removeClass('active');
            next_url.addClass('active');

        });

        $( ".block_title_icon .left_slide" ).on('click', function(){
            var block_gallery = $(this).closest('.title_icon');
            var active_url = block_gallery.find('.dot_nav.active');
            var next_url = active_url.prev();
            if( next_url.length == 0 ) {
               next_url = block_gallery.find('.dot_nav').last();
            }        
            var big_img = block_gallery.find('.wrapp_title_icon');
    
            big_img.find('img').fadeOut('slow').remove();
            big_img.prepend("<img src="+next_url.attr( "data-img-src" )+" />");
            active_url.removeClass('active');
            next_url.addClass('active');

        });

        //when open tab go to top of page
        $('#tabs_block .collapse').on('shown.bs.collapse', function(e) {
            var $card = $(this).closest('.card');
            $('html,body').animate({
                scrollTop: $card.offset().top - 10
            }, 800);

        });
        
    }

    // change image in gallery
    $('.img_gallery .img_prew img').on('click', function(){
        
        var url = $(this).attr( "src" );       
        $('.img_gallery .img_prew ul li').removeClass('active');

        $(this).parent('li').addClass('active');
        var big_img = $(this).closest('.img_gallery').find('.current_img');

        big_img.find('img').fadeOut('slow').remove();
        big_img.prepend("<img src="+url+" />");
        
    }); 

    //collapse footer menu item on mobile
    if ($(window).width() < 575) {
        $("#footer_nav_block .menu_header").on('click', function(){
            $(this).siblings(".mobile-collapse").toggle();
        });
    }

    function set_active_url(url){

        var menu_a = $('#main_menu a');
        menu_a.each(function( index ) {

            var this_item = $( this );

            if(url.indexOf('_faq') >= 2 || url.indexOf('support') >= 2 ){
                $('#support_link').addClass('active');
                return false;
            }

            if(url.indexOf('sales') >= 2 ){
                console.log('faq');
                $('#sales_link').addClass('active');
                return false;
            }

            if (url.indexOf(this_item.attr('href')) >= 10){

                if(this_item.hasClass('dropdown-item')){
                    var top_item = this_item.closest('li.nav-item.dropdown').find('a.nav-link.dropdown-toggle');
                    top_item.addClass('active');
                }else{
                    
                }
            }
        });
    }
    

});    
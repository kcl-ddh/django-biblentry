(function() {

    tinymce.create('tinymce.plugins.BiblEntryPlugin', {
        /**
         * Initializes the plugin, this will be executed after the
         * plugin has been created.
         * This call is done before the editor instance has finished
         * it's initialization so use the onInit event of the editor
         * instance to intercept that event.
         *
         * @param {tinymce.Editor} ed Editor instance that the plugin is initialized in.
         * @param {string} url Absolute URL to where the plugin is located.
         */
        init : function(ed, url) {
            var buttons = [
		{'name': 'Author', 'class_name': 'tei-author', 'unique': 0, 'color': 0x800000}, 
		{'name': 'Editor', 'class_name': 'tei-editor', 'unique': 0, 'color': 0xFFA500}, 
		{'name': 'TitleArticle', 'class_name': 'tei-title teia-level__a', 'unique': 1, 'color': 0x0000FF}, 
		{'name': 'TitleMonograph', 'class_name': 'tei-title teia-level__m', 'unique': 1, 'color': 0x0000FF}, 
		{'name': 'Date', 'class_name': 'tei-date', 'unique': 1, 'color': 0x008000},
                {'name': 'Unmark', 'class_name': 'NONE', 'unique': false},
            ];

            // Load custom CSS files.
            ed.onInit.add(function() {
                if (ed.settings.content_css !== false) {
		    ed.dom.loadCSS(url + "/css/buttons.css");
	        }
	    });

            function spanSelection(ed, span_class_name, unique) {
		/**
	         * Remove all existing mark-up inside the selection.
		 * Remove spans with same class in the editor.
		 * Remove spans with same class overlapping this element.
                 */
		if (ed.selection.isCollapsed()) return;
                
		if (unique === null) unique = false;
		
		unmarkWithinAndThroughSelection();
				
		if (unique) removeAllSpans(ed, span_class_name);
		var sel_cont = ed.selection.getContent();
		ed.selection.setContent('<span class="' + span_class_name + '">' + sel_cont + '</span>');				
	    }

            function removeAllSpans(ed, span_class_name) {
                ed.dom.remove(ed.dom.select('span.' + span_class_name), true);
            }

	    function unmark(span_only) {
		if (span_only === null) span_only = false;
		for (var node = ed.selection.getNode(); node !== null; node = node.parentNode) {
		    if (node.attributes && node.attributes.getNamedItem("class") && node.attributes.getNamedItem("class").value.match(/^tei-/)) {
			if (span_only && node.tagName != 'SPAN') {
			    break;
			}
			// Found an element with tei class.
			// Remove all the children with tei class.
                        /**
                         * Django's admin has its own privately
                         * namespace jQuery, and this might as well be
                         * used. If this editor is to be used outside
                         * of the admin, this will need to be changed
                         * (or the admin's jQuery used).
                         */
			django.jQuery(node).find('[class|=tei]').each(function() {
                            ed.dom.remove(this,true);
                        });
			// Remove the element.
			ed.dom.remove(node, true);
			break;
		    }
		}			
	    }

	    function unmarkWithinAndThroughSelection() {
		var bm = ed.selection.getBookmark();
		ed.selection.collapse();
		unmark(true);
		ed.selection.moveToBookmark(bm);
		bm = ed.selection.getBookmark();
		ed.selection.collapse(true);
		unmark(true);
		ed.selection.moveToBookmark(bm);
		bm = ed.selection.getBookmark();
		// Remove all the elements in the current selection.
		var sel_cont = ed.selection.getContent();
		sel_cont = sel_cont.replace(/<[^>]*>/g, '');
		ed.selection.setContent(sel_cont);
		ed.selection.moveToBookmark(bm);
	    }

	    ed.addCommand('mceBiblEntryAuthor', function() {
                spanSelection(ed, 'tei-author'); });
	    ed.addCommand('mceBiblEntryEditor', function() {
                spanSelection(ed, 'tei-editor'); });
	    ed.addCommand('mceBiblEntryTitleArticle', function() {
                spanSelection(ed, 'tei-title teia-level__a', true); });
	    ed.addCommand('mceBiblEntryTitleMonograph', function() {
                spanSelection(ed, 'tei-title teia-level__m', true); });
	    ed.addCommand('mceBiblEntryDate', function() {
                spanSelection(ed, 'tei-date', true); });
            ed.addCommand('mceBiblEntryUnmark', function() {
                unmark(true);
            });

	    // Register the command and button for each control.
	    for (i = 0; i < buttons.length; i++) {
		var name = buttons[i].name;
		var namelc = name.toLowerCase(); 
		ed.addButton('BiblEntry' + namelc, {
		    title : 'biblentry.' + namelc,
		    cmd : 'mceBiblEntry' + name,
		    image : url + '/img/' + namelc + '.gif'
		});
	    }

	    // Highlight and enable buttons depending on the current selection.
	    ed.onNodeChange.add(function(ed, cm, n) {
		var inherited_classes = '|';
		for (var node = n; node !== null; node = node.parentNode) {
		    inherited_classes += ed.dom.getAttrib(node, 'class')+'|';
		}

		var has_selection = !ed.selection.isCollapsed();
		for (i = 0; i < buttons.length; i++) {
		    var name = buttons[i].name;
		    var namelc = name.toLowerCase(); 
		    b = cm.get('BiblEntry' + namelc);
		    if (b) {
			b.setDisabled(!has_selection);
			b.setState('Selected', inherited_classes.indexOf(buttons[i].class_name) != -1);
		    }
		}
		
		cm.setDisabled('BiblEntryunmark', !ed.selection.isCollapsed());
	    });
	},

        /**
         * Creates control instances based in the incoming name. This
         * method is normally not needed since the addButton method of
         * the tinymce.Editor class is a more easy way of adding
         * buttons but you sometimes need to create more complex
         * controls like listboxes, split buttons etc then this method
         * can be used to create those.
         *
         * @param {String} n Name of the control to create.
         * @param {tinymce.ControlManager} cm Control manager to use inorder to create new control.
         * @return {tinymce.ui.Control} New control instance or null if no control was created.
         */
        createControl : function(n, cm) {
            return null;
        },

        /**
         * Returns information about the plugin as a name/value array.
         * The current keys are longname, author, authorurl, infourl
         * and version.
         *
         * @return {Object} Name/value array containing information about the plugin.
         */
        getInfo : function() {
            return {
                longname : 'BiblEntry plugin',
                author : 'Geoffroy Noel',
                version : '1.0'
            };
        }
    });

    // Register plugin.
    tinymce.PluginManager.add('biblentry', tinymce.plugins.BiblEntryPlugin);

})();
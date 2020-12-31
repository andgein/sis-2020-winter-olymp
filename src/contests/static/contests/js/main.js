(function($) {

	"use strict";

	var fullHeight = function() {

		$('.js-fullheight').css('height', $(window).height());
		$(window).resize(function(){
			$('.js-fullheight').css('height', $(window).height());
		});

	};
	fullHeight();

	$('.close-submission-team-selection').multiselect();

	$(".sabotage-team-selection").each(function(idx, obj) {
		let $this = $(obj);
		if ($this.data("maximum")) {
			let maximum = $this.data("maximum");
			$this.multiselect({
				onChange: function (option, checked) {
					// Get selected options.
					let selectedOptions = $this.find('option:selected');

					if (selectedOptions.length >= maximum) {
						// Disable all other checkboxes.
						let nonSelectedOptions = $this.find('option').filter(function () {
							return !$(this).is(':selected');
						});

						nonSelectedOptions.each(function () {
							let input = $('input[value="' + $(this).val() + '"]');
							input.prop('disabled', true);
							input.closest('.multiselect-option').addClass('disabled');
						});
					} else {
						// Enable all checkboxes.
						$this.find('option').each(function () {
							let input = $('input[value="' + $(this).val() + '"]');
							input.prop('disabled', false);
							input.closest('.multiselect-option').removeClass('disabled');
						});
					}
				},
				nonSelectedText: "Выберите команды-жертвы (не больше " + maximum + ")"
			});
		}
	});

	window.openProblem = function(problem_id) {
		let $this = $(".problem-on-map[data-problem-id=" + problem_id+ "]");
		let $modal = $(".problem-modal");
		$modal.find(".problem-name").text($this.data("problem-index") + ". " + $this.data("problem-name") + " (до " + $this.data("max-score") + " баллов)");
		$modal.find(".problem-statement").html($this.data("statement"));
		$modal.find(".problem-input-data-link a").attr("href", $this.data("input-data-link"));
		$modal.find(".problem-input-data-link").toggle($this.data("has-input"))
		let $form = $modal.find("form");
		if ($form) {
			$form.attr("action", $form.data("url-template").replace("problems/0", "problems/" + $this.data("problem-id")));
		}

		let newHref = window.location.href;
		if (newHref.indexOf("/problems/") === -1) {
			newHref = window.location.href + "problems/" + $this.data("problem-id") + "/";
		}
		history.pushState({}, "", newHref);

		$modal.modal("toggle");
		MathJax.typeset();

		$modal.on('hidden.bs.modal', function (e) {
			let newHref = window.location.href;
			if (newHref.indexOf("/problems/") !== -1) {
				newHref = newHref.substring(0, newHref.lastIndexOf('/'));
				newHref = newHref.substring(0, newHref.lastIndexOf('/'));
				newHref = newHref.substring(0, newHref.lastIndexOf('/'));
				newHref = newHref + "/"
			}
			history.pushState({}, "", newHref);
			$modal.find(".problem-status").remove();
		});
	}

	$(".problem-on-map:not(.solved)").click(function(e) {
		e.preventDefault();
		let $this = $(this);
		openProblem($this.data("problem-id"));
	});

	$(".close-door-button").click(function(e) {
		e.preventDefault();
		$(".main-panel").hide();
		$(".close-door-panel").show();
	});

	$(".sabotage-button").click(function(e) {
		e.preventDefault();
		$(".main-panel").hide();
		$(".sabotage-panel").show();
	});

	$(".sidebar-button-back").click(function(e) {
		e.preventDefault();
		$(".main-panel").show();
		$(".close-door-panel").hide();
		$(".sabotage-panel").hide();
		$('.panel-error').text("")
	})

	window.checkSabotages = function(contest_id) {
		let url = "/contests/" + contest_id + "/sabotages/check/";
		$.getJSON(url, function (data) {
			if (data.sabotages.length === 0)
				return;
			let first = data.sabotages[0];
			let old = JSON.parse(localStorage.getItem("sabotages") || "[]")
			if (old.indexOf(first) === -1) {
				old.push(first);
				localStorage.setItem("sabotages", JSON.stringify(old))

				if ("serviceWorker" in navigator) {
					navigator.serviceWorker.register('/sw.js', {
						scope: '/',
					}).then(function () {
						navigator.serviceWorker.ready.then(function(swreg) {
							swreg.showNotification('Саботаж на корабле!', {body: "Вам объявили саботаж. Срочно выполните задание или потеряете баллы."});
						});
					});
				}

				document.location.reload();
			}
		});
	}

	$('[data-toggle="tooltip"]').tooltip();

	Notification.requestPermission();

})(jQuery);
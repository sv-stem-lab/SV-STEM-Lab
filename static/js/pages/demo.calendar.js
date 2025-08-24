!function (l) {
	"use strict";
	function e() {
		this.$body = l("body"),
		this.$modal = new bootstrap.Modal(document.getElementById("event-modal"), {backdrop: "static"}),
		this.$calendar = l("#calendar"),
		this.$formEvent = l("#form-event"),
		this.$btnNewEvent = l("#btn-new-event"),
		this.$btnDeleteEvent = l("#btn-delete-event"),
		this.$btnSaveEvent = l("#btn-save-event"),
		this.$btnSaveEvents = l("#btn-save-events"),
		this.$modalTitle = l("#modal-title"),
		this.$calendarObj = null,
		this.$selectedEvent = null,
		this.$newEventData = null
	}

	// Function to save events
	e.prototype.saveEvent = async function(events) {
		try {
			const userID = window.userID;
			
			const requestData = {
				schedule: events,
				userID: userID
			};
			
			const response = await fetch('/save-event', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(requestData)
			});
			const result = await response.json();
			if (!response.ok) {
				throw new Error(result.error || 'Failed to save events');
			}
			return result;
		} catch (error) {
			console.error('Error saving events:', error);
			throw error;
		}
	};

	// Function to show success toast
	e.prototype.showSuccessToast = function(message) {
		const successToast = document.getElementById('successToast');
		const successMessage = document.getElementById('successMessage');
		if (successMessage) {
			successMessage.textContent = message;
		}
		const toast = new bootstrap.Toast(successToast);
		toast.show();
	};

	// Function to show error toast
	e.prototype.showErrorToast = function(message) {
		const errorToast = document.getElementById('errorToast');
		const errorMessage = document.getElementById('errorMessage');
		if (errorMessage) {
			errorMessage.textContent = message;
		}
		const toast = new bootstrap.Toast(errorToast);
		toast.show();
	};

	e.prototype.onEventClick = function (e) {
		this.$formEvent[0].reset(),
		this.$formEvent.removeClass("was-validated"),
		this.$newEventData = null,
		this.$btnDeleteEvent.show(),
		this.$modalTitle.text("Edit Event"),
		this.$modal.show(),
		this.$selectedEvent = e.event,
		l("#event-title").val(this.$selectedEvent.title),
		l("#event-info").val(this.$selectedEvent.extendedProps?.info || ''),
		l("#event-category").val(this.$selectedEvent.classNames[0])
	},
	e.prototype.onSelect = function (e) {
		this.$formEvent[0].reset(),
		this.$formEvent.removeClass("was-validated"),
		this.$selectedEvent = null,
		this.$newEventData = e,
		this.$btnDeleteEvent.hide(),
		this.$modalTitle.text("Add New Event"),
		this.$modal.show(),
		this.$calendarObj.unselect()
	},
	e.prototype.init = function () {
		var e = new Date(l.now());
		new FullCalendar.Draggable(document.getElementById("external-events"), {
			itemSelector: ".external-event",
			eventData: function (e) {
				return {title: e.innerText, className: l(e).data("class")}
			}
		});

		// Process schedules and create events
		var scheduleEvents = [];
		if (window.schedules) {
			window.schedules.forEach(function(schedule) {
				// Create base date from the ISO string
				var baseDate = new Date(schedule.start);
				var baseEndDate = schedule.end ? new Date(schedule.end) : null;
				
				// Check if this should be an all-day event
				var isAllDay = !schedule.end && baseDate.getUTCHours() === 7 && baseDate.getUTCMinutes() === 0;
				
				// Create events for each session
				for (var i = 0; i < schedule.session; i++) {
					var eventDate = new Date(baseDate);
					var eventEndDate = baseEndDate ? new Date(baseEndDate) : null;
					
					// Add one week for each session
					eventDate.setDate(eventDate.getDate() + (i * 7));
					if (eventEndDate) {
						eventEndDate.setDate(eventEndDate.getDate() + (i * 7));
					}
					
					scheduleEvents.push({
						title: schedule.title,
						start: eventDate,
						end: eventEndDate,
						allDay: isAllDay,
						className: schedule.className,
						extendedProps: {
							info: schedule.info || ''
						}
					});
				}
			});
		}

		var t = scheduleEvents,
			a = this;

		// Function to determine header layout based on screen width
		function getHeaderToolbar() {
			if (window.innerWidth < 768) {
				return {
					left: 'prev,next today',
					center: 'title',
					right: ''
				};
			}
			return {
				left: 'prev,next today',
				center: 'title',
				right: 'dayGridMonth,timeGridWeek,timeGridDay,listMonth'
			};
		}

		// Function to handle view buttons visibility
		function handleViewButtons() {
			const viewButtons = document.querySelector('.calendar-view-buttons');
			if (window.innerWidth < 768) {
				if (!viewButtons) {
					// Create view buttons if they don't exist
					const newViewButtons = document.createElement('div');
					newViewButtons.className = 'calendar-view-buttons mt-2 text-center';
					newViewButtons.innerHTML = `
						<button class="btn btn-sm btn-success" data-view="dayGridMonth">Month</button>
						<button class="btn btn-sm btn-success" data-view="timeGridWeek">Week</button>
						<button class="btn btn-sm btn-success" data-view="timeGridDay">Day</button>
						<button class="btn btn-sm btn-success" data-view="listMonth">List</button>
					`;
					a.$calendar.after(newViewButtons);

					// Add click handlers for view buttons
					newViewButtons.querySelectorAll('button').forEach(button => {
						button.addEventListener('click', () => {
							a.$calendarObj.changeView(button.dataset.view);
							newViewButtons.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
							button.classList.add('active');
						});
					});
				} else {
					viewButtons.style.display = 'block';
				}
			} else if (viewButtons) {
				viewButtons.style.display = 'none';
			}
		}

		a.$calendarObj = new FullCalendar.Calendar(a.$calendar[0], {
			slotDuration: "00:15:00",
			slotMinTime: "08:00:00",
			slotMaxTime: "19:00:00",
			themeSystem: "bootstrap",
			bootstrapFontAwesome: !1,
			buttonText: {
				today: "Today",
				month: "Month",
				week: "Week",
				day: "Day",
				list: "List",
				prev: "Prev",
				next: "Next"
			},
			initialView: "dayGridMonth",
			handleWindowResize: !0,
			height: l(window).height() - 200,
			headerToolbar: getHeaderToolbar(),
			initialEvents: t,
			editable: !0,
			droppable: !0,
			selectable: !0,
			dateClick: function (e) {
				a.onSelect(e)
			},
			eventClick: function (e) {
				a.onEventClick(e)
			}
		}),
		a.$calendarObj.render(),
		a.$btnNewEvent.on("click", function (e) {
			a.onSelect({
				date: new Date,
				allDay: !0
			})
		}),
		a.$formEvent.on("submit", function (e) {
			e.preventDefault();
			var n = a.$formEvent[0];
			
			if (n.checkValidity()) {
				// Get form values
				var eventTitle = l("#event-title").val();
				var eventInfo = l("#event-info").val();
				var eventCategory = l("#event-category").val();
				
				if (a.$selectedEvent) {
					// Update existing event
					a.$selectedEvent.setProp("title", eventTitle);
					a.$selectedEvent.setProp("classNames", [eventCategory]);
					a.$selectedEvent.setExtendedProp("info", eventInfo);
					
					a.showSuccessToast('Event updated successfully!');
				} else {
					// Create new event
					var newEvent = {
						title: eventTitle,
						start: a.$newEventData.date,
						allDay: a.$newEventData.allDay,
						className: eventCategory,
						extendedProps: {
							info: eventInfo
						}
					};
					
					a.$calendarObj.addEvent(newEvent);
					
					a.showSuccessToast('Event created successfully!');
				}
				
				a.$modal.hide();
			} else {
				e.stopPropagation();
				n.classList.add("was-validated");
			}
		}),
		l(a.$btnDeleteEvent.on("click", function (e) {
			a.$selectedEvent && (a.$selectedEvent.remove(), a.$selectedEvent = null, a.$modal.hide())
		})),
		l(a.$btnSaveEvents.on("click", async function (e) {
			try {
				// Get all current events
				const allEvents = a.$calendarObj.getEvents().map(event => ({
					title: event.title,
					start: event.start.toISOString(),
					end: event.end ? event.end.toISOString() : null,
					className: event.classNames[0],
					session: 1,
					info: event.extendedProps?.info || ''
				}));
				
				// Save all events
				await a.saveEvent(allEvents);
				a.showSuccessToast('Events saved successfully!');
			} catch (error) {
				console.error('Failed to save events:', error);
				a.showErrorToast('Failed to save events. Please try again.');
			}
		}))

		// Initial setup of view buttons
		handleViewButtons();

		// Update header and view buttons on window resize
		window.addEventListener('resize', () => {
			a.$calendarObj.setOption('headerToolbar', getHeaderToolbar());
			handleViewButtons();
		});
	},
	l.CalendarApp = new e,
	l.CalendarApp.Constructor = e
}(window.jQuery),
function () {
	"use strict";
	window.jQuery.CalendarApp.init()
}();

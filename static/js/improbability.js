      function adjustBrandText() {
          var brandText = document.querySelector('.brand-text');
          if (window.innerWidth > 1200) {
              brandText.textContent = 'Improbability Labs - SMS AI Assistant';
          } else {
              brandText.textContent = 'SMS AI Assistant'; // You can adjust this if different text is needed for smaller sizes
          }
      }


      function adjustFaqTitle() {
          var brandText = document.querySelector('.faq-page-title');
          if (window.innerWidth >= 768) {
              brandText.textContent = 'Frequently Asked Questions';
          } else {
              brandText.textContent = 'FAQ'; // You can adjust this if different text is needed for smaller sizes
          }
      }

      // Run both functions on load and resize
      window.addEventListener('load', adjustBrandText);
      window.addEventListener('resize', adjustBrandText);

      window.addEventListener('load', adjustFaqTitle);
      window.addEventListener('resize', adjustFaqTitle);

      function updateStates(country) {
          const stateSelect = document.getElementById('state');
          stateSelect.innerHTML = ''; // Clear existing options
          if (country === 'USA') {
              // List of states for USA with full names and abbreviations
              const states = [{
                  abbreviation: 'AL',
                  name: 'Alabama'
              }, {
                  abbreviation: 'AK',
                  name: 'Alaska'
              }, {
                  abbreviation: 'AZ',
                  name: 'Arizona'
              }, {
                  abbreviation: 'AR',
                  name: 'Arkansas'
              }, {
                  abbreviation: 'CA',
                  name: 'California'
              }, {
                  abbreviation: 'CO',
                  name: 'Colorado'
              }, {
                  abbreviation: 'CT',
                  name: 'Connecticut'
              }, {
                  abbreviation: 'DE',
                  name: 'Delaware'
              }, {
                  abbreviation: 'FL',
                  name: 'Florida'
              }, {
                  abbreviation: 'GA',
                  name: 'Georgia'
              }, {
                  abbreviation: 'HI',
                  name: 'Hawaii'
              }, {
                  abbreviation: 'ID',
                  name: 'Idaho'
              }, {
                  abbreviation: 'IL',
                  name: 'Illinois'
              }, {
                  abbreviation: 'IN',
                  name: 'Indiana'
              }, {
                  abbreviation: 'IA',
                  name: 'Iowa'
              }, {
                  abbreviation: 'KS',
                  name: 'Kansas'
              }, {
                  abbreviation: 'KY',
                  name: 'Kentucky'
              }, {
                  abbreviation: 'LA',
                  name: 'Louisiana'
              }, {
                  abbreviation: 'ME',
                  name: 'Maine'
              }, {
                  abbreviation: 'MD',
                  name: 'Maryland'
              }, {
                  abbreviation: 'MA',
                  name: 'Massachusetts'
              }, {
                  abbreviation: 'MI',
                  name: 'Michigan'
              }, {
                  abbreviation: 'MN',
                  name: 'Minnesota'
              }, {
                  abbreviation: 'MS',
                  name: 'Mississippi'
              }, {
                  abbreviation: 'MO',
                  name: 'Missouri'
              }, {
                  abbreviation: 'MT',
                  name: 'Montana'
              }, {
                  abbreviation: 'NE',
                  name: 'Nebraska'
              }, {
                  abbreviation: 'NV',
                  name: 'Nevada'
              }, {
                  abbreviation: 'NH',
                  name: 'New Hampshire'
              }, {
                  abbreviation: 'NJ',
                  name: 'New Jersey'
              }, {
                  abbreviation: 'NM',
                  name: 'New Mexico'
              }, {
                  abbreviation: 'NY',
                  name: 'New York'
              }, {
                  abbreviation: 'NC',
                  name: 'North Carolina'
              }, {
                  abbreviation: 'ND',
                  name: 'North Dakota'
              }, {
                  abbreviation: 'OH',
                  name: 'Ohio'
              }, {
                  abbreviation: 'OK',
                  name: 'Oklahoma'
              }, {
                  abbreviation: 'OR',
                  name: 'Oregon'
              }, {
                  abbreviation: 'PA',
                  name: 'Pennsylvania'
              }, {
                  abbreviation: 'RI',
                  name: 'Rhode Island'
              }, {
                  abbreviation: 'SC',
                  name: 'South Carolina'
              }, {
                  abbreviation: 'SD',
                  name: 'South Dakota'
              }, {
                  abbreviation: 'TN',
                  name: 'Tennessee'
              }, {
                  abbreviation: 'TX',
                  name: 'Texas'
              }, {
                  abbreviation: 'UT',
                  name: 'Utah'
              }, {
                  abbreviation: 'VT',
                  name: 'Vermont'
              }, {
                  abbreviation: 'VA',
                  name: 'Virginia'
              }, {
                  abbreviation: 'WA',
                  name: 'Washington'
              }, {
                  abbreviation: 'WV',
                  name: 'West Virginia'
              }, {
                  abbreviation: 'WI',
                  name: 'Wisconsin'
              }, {
                  abbreviation: 'WY',
                  name: 'Wyoming'
              }];
              states.forEach(state => {
                  const option = document.createElement('option');
                  option.value = state.abbreviation;
                  option.text = state.name;
                  stateSelect.appendChild(option);
              });
          } else if (country === 'CAN') {
              // List of provinces for Canada with full names and abbreviations
              const provinces = [{
                  abbreviation: 'AB',
                  name: 'Alberta'
              }, {
                  abbreviation: 'BC',
                  name: 'British Columbia'
              }, {
                  abbreviation: 'MB',
                  name: 'Manitoba'
              }, {
                  abbreviation: 'NB',
                  name: 'New Brunswick'
              }, {
                  abbreviation: 'NL',
                  name: 'Newfoundland and Labrador'
              }, {
                  abbreviation: 'NT',
                  name: 'Northwest Territories'
              }, {
                  abbreviation: 'NS',
                  name: 'Nova Scotia'
              }, {
                  abbreviation: 'NU',
                  name: 'Nunavut'
              }, {
                  abbreviation: 'ON',
                  name: 'Ontario'
              }, {
                  abbreviation: 'PE',
                  name: 'Prince Edward Island'
              }, {
                  abbreviation: 'QC',
                  name: 'Quebec'
              }, {
                  abbreviation: 'SK',
                  name: 'Saskatchewan'
              }, {
                  abbreviation: 'YT',
                  name: 'Yukon'
              }];
              provinces.forEach(province => {
                  const option = document.createElement('option');
                  option.value = province.abbreviation;
                  option.text = province.name;
                  stateSelect.appendChild(option);
              });
          }
      }

      document.getElementById('user-mobile').addEventListener('input', function() {
          const inputElement = this;
          let phoneNumber = inputElement.value.replace(/\D/g, ''); // Remove all non-numeric characters

          // Limit to 10 digits for US and Canadian numbers
          if (phoneNumber.length > 10) {
              phoneNumber = phoneNumber.slice(0, 10);
          }

          // Ensure the area code does not start with 0 or 1
          if (phoneNumber.length >= 1 && (phoneNumber.slice(0, 1) === '0' || phoneNumber.slice(0, 1) === '1')) {
              phoneNumber = phoneNumber.slice(1);
          }

          // Apply formatting only when all 10 digits are present
          if (phoneNumber.length === 10) {
              phoneNumber = '(' + phoneNumber.slice(0, 3) + ') ' + phoneNumber.slice(3, 6) + '-' + phoneNumber.slice(6);
          }

          inputElement.value = phoneNumber; // Update the input value with formatted or unformatted number
      });

      document.getElementById('card-cc').addEventListener('input', function(e) {
          var input = e.target.value.replace(/\D/g, '').substring(0, 16); // Remove non-digits and limit to 16 characters
          var formatted = input.replace(/(\d{4})(?=\d)/g, '$1 '); // Add a space after every 4 digits
          e.target.value = formatted;
      });


      document.getElementById('card-name').addEventListener('input', function(e) {
          var input = e.target.value.replace(/[^A-Za-z ]/g, ''); // Remove non-alphabetic characters
          e.target.value = input;
      });

      document.getElementById('country').addEventListener('change', function() {
          document.getElementById('billing-zip').value = ''; // Clear postal code field when country changes
      });

      document.getElementById('billing-zip').addEventListener('input', function(e) {
          const country = document.getElementById('country').value;
          let input = e.target.value.toUpperCase(); // Convert to uppercase
          let formattedInput = '';

          if (country === 'USA') {
              // Remove all non-digit characters and limit to 5 digits for US ZIP code
              formattedInput = input.replace(/[^0-9]/g, '').substring(0, 5);
          } else if (country === 'CAN') {
              // Remove all non-alphanumeric characters
              input = input.replace(/[^A-Z0-9]/g, '');

              // Format as Canadian postal code (A1A 1A1)
              if (/^[A-Z]\d[A-Z]\d[A-Z]\d$/.test(input)) {
                  formattedInput = input.substring(0, 3) + ' ' + input.substring(3, 6);
              } else {
                  // Allow typing only valid characters for Canadian postal codes
                  formattedInput = input.split('').filter((char, index) => {
                      // Allow only first 6 characters and follow the pattern letter, digit, letter, etc.
                      return index < 6 && ((index % 2 === 0 && /[A-Z]/.test(char)) || (index % 2 !== 0 && /\d/.test(char)));
                  }).join('');
              }
          }

          e.target.value = formattedInput;
      });


      document.getElementById('card-exp').addEventListener('input', function(e) {
          var input = e.target.value.replace(/\D/g, '').substring(0, 4); // Remove non-digits and limit to 4 characters
          var month = input.substring(0, 2); // Extract the first two characters as the month
          var year = input.substring(2, 4); // Extract the next two characters as the year

          // Ensure the month is between 01 and 12
          if (month.length === 2 && (month < '01' || month > '12')) {
              month = ''; // If not, clear the month
              year = ''; // Clear year as well since month is invalid
          }

          // Apply formatting only when all 4 digits are present and the month is valid
          e.target.value = (month && year.length === 2) ? (month + '/' + year) : month + year;
      });

      document.querySelectorAll('input[name="subscriptionOption"]').forEach(radio => {
          radio.addEventListener('change', function() {
              const details = document.querySelector('.purchase-details-price'); // Using class selector
              const detailstitle = document.querySelector('.purchase-details-price-title'); // Using class selector
              if (this.checked) {
                  details.style.display = 'block';
                  detailstitle.style.display = 'block';
                  document.querySelector('.subscription-name').textContent = this.dataset.product;
                  document.querySelector('.plan-final').textContent = `${this.dataset.cost} ${this.dataset.currency} per ${this.dataset.interval}`;
              } else {
                  details.style.display = 'none'; // Optionally hide the details when another option is unchecked
              }
          });
      });

      // Function to allow only numbers in the CVV field and limit to 4 characters
      document.getElementById('card-cvc').addEventListener('input', function(e) {
          e.target.value = e.target.value.replace(/\D/g, '').substring(0, 4);
      });


      $.fn.pageMe = function(opts) {
          var $this = this,
              defaults = {
                  perPage: 7,
                  showPrevNext: false,
                  numbersPerPage: 5,
                  hidePageNumbers: false
              },
              settings = $.extend(defaults, opts);

          var listElement = $this;
          var perPage = settings.perPage;
          var children = listElement.children();
          var pager = $('.pagination');

          if (typeof settings.childSelector != "undefined") {
              children = listElement.find(settings.childSelector);
          }

          if (typeof settings.pagerSelector != "undefined") {
              pager = $(settings.pagerSelector);
          }

          var numItems = children.size();
          var numPages = Math.ceil(numItems / perPage);

          pager.data("curr", 0);

          if (settings.showPrevNext) {
              $('<li><a href="#" class="prev_link">Â«</a></li>').appendTo(pager);
          }

          var curr = 0;
          while (numPages > curr && (settings.hidePageNumbers == false)) {
              $('<li><a href="#" class="page_link">' + (curr + 1) + '</a></li>').appendTo(pager);
              curr++;
          }

          if (settings.numbersPerPage > 1) {
              $('.page_link').hide();
              $('.page_link').slice(pager.data("curr"), settings.numbersPerPage).show();
          }

          if (settings.showPrevNext) {
              $('<li><a href="#" class="next_link">Â»</a></li>').appendTo(pager);
          }

          pager.find('.page_link:first').addClass('active');
          pager.find('.prev_link').hide();
          if (numPages <= 1) {
              pager.find('.next_link').hide();
          }
          pager.children().eq(1).addClass("active");

          children.hide();
          children.slice(0, perPage).show();

          pager.find('li .page_link').click(function() {
              var clickedPage = $(this).html().valueOf() - 1;
              goTo(clickedPage, perPage);
              return false;
          });
          pager.find('li .prev_link').click(function() {
              previous();
              return false;
          });
          pager.find('li .next_link').click(function() {
              next();
              return false;
          });

          function previous() {
              var goToPage = parseInt(pager.data("curr")) - 1;
              goTo(goToPage);
          }

          function next() {
              goToPage = parseInt(pager.data("curr")) + 1;
              goTo(goToPage);
          }

          function goTo(page) {
              var startAt = page * perPage,
                  endOn = startAt + perPage;

              children.css('display', 'none').slice(startAt, endOn).show();

              if (page >= 1) {
                  pager.find('.prev_link').show();
              } else {
                  pager.find('.prev_link').hide();
              }

              if (page < (numPages - 1)) {
                  pager.find('.next_link').show();
              } else {
                  pager.find('.next_link').hide();
              }

              pager.data("curr", page);

              if (settings.numbersPerPage > 1) {
                  $('.page_link').hide();
                  $('.page_link').slice(page, settings.numbersPerPage + page).show();
              }

              pager.children().removeClass("active");
              pager.children().eq(page + 1).addClass("active");

          }
      };

      $(document).ready(function() {

          $('#invoices').pageMe({
              pagerSelector: '#invoicePager',
              showPrevNext: true,
              hidePageNumbers: false,
              perPage: 4
          });

      });

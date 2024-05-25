let currentPageSms = sessionStorage.getItem('currentPageSms') ? parseInt(sessionStorage.getItem('currentPageSms')) : 0;
let currentPageInvoice = sessionStorage.getItem('currentPageInvoice') ? parseInt(sessionStorage.getItem('currentPageInvoice')) : 0;

$.fn.pageMe = function(opts) {
    var $this = this,
        defaults = {
            perPage: 7,
            showPrevNext: true,
            numbersPerPage: 3,
            hidePageNumbers: false
        },
        settings = $.extend(defaults, opts);

    var listElement = $this,
        perPage = settings.perPage,
        children = listElement.children();

    if (typeof settings.childSelector !== "undefined") {
        children = listElement.find(settings.childSelector);
    }

    if (typeof settings.pagerSelector !== "undefined") {
        var pager = $(settings.pagerSelector);
    } else {
        var pager = $('<ul class="pagination"></ul>').appendTo(listElement.parent());
    }

    // Clear existing pagination elements
    pager.empty();

    var numItems = children.length;
    var numPages = Math.ceil(numItems / perPage);

    pager.data("curr", settings.currentPage || 0);

    if (settings.showPrevNext) {
        $('<li><a href="#" class="prev_link">«</a></li>').appendTo(pager);
    }

    for (var i = 0; i < numPages; i++) {
        $('<li><a href="#" class="page_link">' + (i + 1) + '</a></li>').appendTo(pager);
    }

    if (settings.showPrevNext) {
        $('<li><a href="#" class="next_link">»</a></li>').appendTo(pager);
    }

    pager.find('.page_link:first').addClass('active');
    pager.find('.prev_link').hide();
    if (numPages <= settings.numbersPerPage) {
        pager.find('.next_link').hide();
    }

    children.hide();
    children.slice(0, perPage).show();

    pager.find('li .page_link').click(function() {
        var clickedPage = $(this).html().valueOf() - 1;
        goTo(clickedPage);
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
        var goToPage = parseInt(pager.data("curr")) + 1;
        goTo(goToPage);
    }

    function goTo(page) {
        var startAt = page * perPage,
            endOn = startAt + perPage;

        children.css('display', 'none').slice(startAt, endOn).show();

        pager.data("curr", page);

        var maxVisiblePages = settings.numbersPerPage;
        var currentPage = page + 1;
        var endPage = numPages;

        pager.find('.page_link').hide();  // Hide all page links initially

        if (numPages <= maxVisiblePages) {
            pager.find('.page_link').slice(0, numPages).show();  // Show all pages if total pages is less than or equal to maxVisiblePages
        } else if (currentPage <= Math.ceil(maxVisiblePages / 2)) {
            pager.find('.page_link').slice(0, maxVisiblePages).show();  // Show first maxVisiblePages pages
        } else if (currentPage >= (endPage - Math.floor(maxVisiblePages / 2))) {
            pager.find('.page_link').slice(endPage - maxVisiblePages, endPage).show();  // Show last maxVisiblePages pages
        } else {
            var startPage = currentPage - Math.floor(maxVisiblePages / 2) - 1;
            var endPage = currentPage + Math.floor(maxVisiblePages / 2);
            pager.find('.page_link').slice(startPage, endPage).show();  // Show middle pages
        }

        pager.children().removeClass("active");
        pager.find('.page_link').removeClass("active");
        pager.children().eq(page + 1).find('a').addClass("active");  // Highlight current page

        if (page == 0) {
            pager.find('.prev_link').hide();  // Hide prev button on first page
        } else {
            pager.find('.prev_link').show();
        }

        if (page == numPages - 1) {
            pager.find('.next_link').hide();  // Hide next button on last page
        } else {
            pager.find('.next_link').show();
        }

        // Save the current page in session storage
        if ($this.attr('id') === 'smsHistory') {
            sessionStorage.setItem('currentPageSms', page);
        } else if ($this.attr('id') === 'invoiceHistory') {
            sessionStorage.setItem('currentPageInvoice', page);
        }
    }

    goTo(settings.currentPage || 0);  // Initialize pagination to the first page or saved page
};

function isMobile() {
    return /iPhone|iPad|iPod|Android/i.test(navigator.userAgent) || window.innerWidth <= 760;
}

function initializePagination() {
    var smsPerPage = isMobile() ? 10 : 20;
    var invoicePerPage = isMobile() ? 6 : 12;

    $('#smsHistory').pageMe({
        pagerSelector: '#smsPager',
        showPrevNext: true,
        hidePageNumbers: false,
        perPage: smsPerPage,
        numbersPerPage: 3,
        currentPage: currentPageSms // Set current page from global variable
    });

    $('#invoiceHistory').pageMe({
        pagerSelector: '#invoicePager',
        showPrevNext: true,
        hidePageNumbers: false,
        perPage: invoicePerPage,
        numbersPerPage: 3,
        currentPage: currentPageInvoice // Set current page from global variable
    });
}

function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this, args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

$(document).ready(function() {
    initializePagination();

    $(window).resize(debounce(function() {
        currentPageSms = $('#smsPager').data('curr') || 0;
        currentPageInvoice = $('#invoicePager').data('curr') || 0;
        initializePagination(); // Reinitialize pagination on window resize
    }, 250));
});











document.addEventListener('DOMContentLoaded', function() {
    var form = document.getElementById("improbability-sms-contact-form");

    async function handleContactSubmit(event) {
        event.preventDefault();
        var successMessage = document.getElementById("improbability-contact-success-message");
        var errorMessage = document.getElementById("improbability-contact-error-message");
        var data = new FormData(event.target);
        var errors = [];

        successMessage.style.display = 'none';
        errorMessage.style.display = 'none';

        // Validate Mobile Number if contact-method is mobile
        var contactMethod = data.get('contact-method');
        var userMobile = document.getElementById('user-mobile').value;

        if (contactMethod === 'mobile') {
            if (!userMobile) {
                errors.push("Mobile number is required when contact method is Mobile.");
            } else {
                const cleanMobileNumber = userMobile.replace(/[^\d]/g, '');
                const mobilePattern = /^[2-9]\d{2}[2-9](?!11)\d{2}\d{4}$/;
                if (!mobilePattern.test(cleanMobileNumber)) {
                    errors.push("Your Mobile Number must be a valid North American number.");
                }
            }
        }

        if (errors.length > 0) {
            errorMessage.innerHTML = `<div style="color: red; border: 1px solid red; padding: 10px;">
                                        <p><strong>Please correct the following errors:</strong></p>
                                        <ul>${errors.map(error => `<li>${error}</li>`).join('')}</ul>
                                    </div>`;
            errorMessage.style.display = 'block';
            return;
        }

        try {
            let response = await fetch(event.target.action, {
                method: form.method,
                body: data,
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (response.ok) {
                successMessage.innerHTML = `<div style="color: green; border: 1px solid green; padding: 10px;">
                                            <p>Your message has been sent successfully!</p>
                                        </div>`;
                successMessage.style.display = 'block';
                form.reset();
            } else {
                let data = await response.json();
                if (data.errors) {
                    errorMessage.innerHTML = `<div style="color: red; border: 1px solid red; padding: 10px;">
                                                <p><strong>Please correct the following errors:</strong></p>
                                                <ul>${data.errors.map(error => `<li>${error.message}</li>`).join('')}</ul>
                                            </div>`;
                } else {
                    errorMessage.innerHTML = `<div style="color: red; border: 1px solid red; padding: 10px;">
                                                <p>Oops! There was a problem submitting your form</p>
                                            </div>`;
                }
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            errorMessage.innerHTML = `<div style="color: red; border: 1px solid red; padding: 10px;">
                                        <p>Oops! There was a problem submitting your form</p>
                                    </div>`;
            errorMessage.style.display = 'block';
        }
    }

    form.addEventListener("submit", handleContactSubmit);
});

document.addEventListener('DOMContentLoaded', function() {
    function adjustFaqTitle() {
        var brandText = document.querySelector('.faq-page-title');
        if (brandText) {  // Check if the element actually exists
            if (window.innerWidth >= 768) {
                brandText.textContent = 'Frequently Asked Questions';
            } else {
                brandText.textContent = 'FAQ'; // You can adjust this if different text is needed for smaller sizes
            }
        } else {
            console.log('Element with class faq-page-title not found on this page.');
        }
    }

    // Run the function once the page has fully loaded
    adjustFaqTitle();
    
    // Add event listeners if the element exists
    if (document.querySelector('.faq-page-title')) {
        window.addEventListener('resize', adjustFaqTitle);
    }
});


document.addEventListener('DOMContentLoaded', function() {
    function adjustBrandText() {
        var brandText = document.querySelector('.brand-text');
        if (brandText) {  // Check if the element actually exists
            if (window.innerWidth > 1200) {
                brandText.textContent = 'Improbability Labs - SMS AI Assistant';
            } else {
                brandText.textContent = 'SMS AI Assistant'; // You can adjust this if different text is needed for smaller sizes
            }
        } else {
            console.log('Element with class brand-text not found on this page.');
        }
    }

    // Run the function once the page has fully loaded
    adjustBrandText();
    
    // Add event listeners if the element exists
    if (document.querySelector('.brand-text')) {
        window.addEventListener('resize', adjustBrandText);
    }
});



function updateStates(country) {
    const stateSelect = document.getElementById('billing-state');
    stateSelect.innerHTML = ''; // Clear existing options

    // Add a default option as the first item
    const defaultOption = document.createElement('option');
    defaultOption.textContent = 'Please select a state/province';
    defaultOption.value = ''; // Make sure this is empty or a specific value that is considered invalid
    defaultOption.selected = true;
    defaultOption.disabled = true; // Optional: make it non-selectable after a selection
    stateSelect.appendChild(defaultOption);

    if (country === 'US') {
        // List of states for USA
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

        // Append each state to the select dropdown
        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state.abbreviation;
            option.text = state.name;
            stateSelect.appendChild(option);
        });
    } else if (country === 'CA') {
        // List of provinces for Canada
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

        // Append each province to the select dropdown
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

      document.getElementById('card-name').addEventListener('input', function(e) {
          var input = e.target.value.replace(/[^A-Za-z ]/g, ''); // Remove non-alphabetic characters
          e.target.value = input;
      });

      document.getElementById('billing-country').addEventListener('change', function() {
          document.getElementById('billing-zip').value = ''; // Clear postal code field when country changes
      });

      document.getElementById('billing-zip').addEventListener('input', function(e) {
          const country = document.getElementById('billing-country').value;
          let input = e.target.value.toUpperCase(); // Convert to uppercase
          let formattedInput = '';

          if (country === 'US') {
              // Remove all non-digit characters and limit to 5 digits for US ZIP code
              formattedInput = input.replace(/[^0-9]/g, '').substring(0, 5);
          } else if (country === 'CA') {
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

document.addEventListener('DOMContentLoaded', function() {
    // Function to update subscription details
    function updateSubscriptionDetails(radio) {
        const details = document.querySelector('.purchase-details-price'); // Using class selector
        const detailstitle = document.querySelector('.purchase-details-price-title'); // Using class selector

        if (radio.checked) {
            details.style.display = 'block';
            detailstitle.style.display = 'block';
            document.querySelector('.subscription-name').textContent = radio.dataset.product;
            
            // Display total cost
            let total = parseFloat(radio.dataset.cost);
            document.querySelector('.plan-final').textContent = `${total.toFixed(2)} ${radio.dataset.currency} per ${radio.dataset.interval}`;
        } else {
            details.style.display = 'none';
        }
    }

    // Attach event listeners to radio buttons
    document.querySelectorAll('input[name="subscriptionOption"]').forEach(radio => {
        radio.addEventListener('change', function() {
            updateSubscriptionDetails(this);
        });

        // Check if the radio button is already selected on page load
        if (radio.checked) {
            updateSubscriptionDetails(radio);
        }
    });
});

 


function validateAssistantDetails() {
    // Reset error display and outline colors if elements exist
    const errorContainer = document.getElementById('assistant-error');
    if (errorContainer) {
        errorContainer.style.display = 'none';
    }

    let isValid = true;
    const errors = [];

    // Validate Assistant's Name
    const assistantName = document.getElementById('assistant-name');
    if (assistantName) {
        if (assistantName.value.length < 3) {
            errors.push("Assistant's Name must be at least 3 characters long.");
            assistantName.style.borderColor = 'red';
            isValid = false;
        } else {
            assistantName.style.borderColor = '';
        }
    }

    // Validate Assistant's Origin
    const assistantOrigin = document.getElementById('assistant-origin');
    if (assistantOrigin) {
        if (assistantOrigin.value.length < 5) {
            errors.push("Assistant's Origin must be at least 5 characters long.");
            assistantOrigin.style.borderColor = 'red';
            isValid = false;
        } else {
            assistantOrigin.style.borderColor = '';
        }
    }

    // Validate dropdowns using the long-label for error messages
    const dropdowns = ['assistant-gender', 'assistant-personality', 'assistant-response-style', 'assistant-demeanor', 'assistant-attitude'];
    dropdowns.forEach(id => {
        const dropdown = document.getElementById(id);
        if (dropdown) {
            // Find the long-label element within the same container as the dropdown
            const longLabel = dropdown.closest('.form-group').querySelector('.long-label');

            if (dropdown.selectedIndex === 0) {
                // Use the innerText of the long-label for the error message
                errors.push(`${longLabel.innerText} is required.`);
                dropdown.style.borderColor = 'red';
                isValid = false;
            } else {
                dropdown.style.borderColor = '';
            }
        }
    });

    
    // Display errors if any
    if (errors.length > 0 && errorContainer) {
        errorContainer.innerHTML = `<div style="color: red; border: 1px solid red; padding: 10px;">
                                    <p><strong>Please correct the following errors:</strong></p>
                                    <ul>${errors.map(error => `<li>${error}</li>`).join('')}</ul>
                                </div>`;
        errorContainer.style.display = 'block';
    } else if (errorContainer) {
        errorContainer.style.display = 'none'; // Hide the container if no errors
    }

    return isValid;
}


function validatePersonalPreferences() {
    // Reset error display and outline colors if elements exist
    const errorContainer = document.getElementById('personal-error');
    if (errorContainer) {
        errorContainer.style.display = 'none';
    }

    let isValid = true;
    const errors = [];

    // Validate Preferred Name
    const userName = document.getElementById('user-name');
    if (userName) {
        if (userName.value.length < 3) {
            errors.push("Your Preferred Name must be at least 3 characters long.");
            userName.style.borderColor = 'red';
            isValid = false;
        } else {
            userName.style.borderColor = '';
        }
    }

    // Validate User Location
    const userLocation = document.getElementById('user-location');
    if (userLocation) {
        if (userLocation.value.length < 5) {
            errors.push("Your Location must be at least 5 characters long.");
            userLocation.style.borderColor = 'red';
            isValid = false;
        } else {
            userLocation.style.borderColor = '';
        }
    }

    // Validate Mobile Number
    const userMobile = document.getElementById('user-mobile');
    if (userMobile) {
        // Remove non-numeric characters from input
        const cleanMobileNumber = userMobile.value.replace(/[^\d]/g, '');

        // North American number format excluding country code
        const mobilePattern = /^[2-9]\d{2}[2-9](?!11)\d{2}\d{4}$/;
        if (!mobilePattern.test(cleanMobileNumber)) {
            errors.push("Your Mobile Number must be a valid North American number.");
            userMobile.style.borderColor = 'red';
            isValid = false;
        } else {
            userMobile.style.borderColor = '';
        }
    }

    // Validate Preferred Communication Language, Title, and Measurement using the long-label for error messages
    const userLanguage = document.getElementById('user-language');
    const userTitle = document.getElementById('user-title');
    const userMeasurement = document.getElementById('user-measurement');

    [userLanguage, userTitle, userMeasurement].forEach(field => {
        if (field) {
            // Find the long-label element within the same container as the field
            const longLabel = field.closest('.form-group').querySelector('.long-label');

            if (field.selectedIndex === 0) {
                // Use the innerText of the long-label for the error message
                errors.push(`Your ${longLabel.innerText} is required.`);
                field.style.borderColor = 'red';
                isValid = false;
            } else {
                field.style.borderColor = '';
            }
        }
    });
    
    // Validate Description
    const userDescription = document.getElementById('user-description');
    if (userDescription) {
        if (userDescription.value.length < 20) {
            errors.push("Your Bio must be descriptive enough (at least 20 characters).");
            userDescription.style.borderColor = 'red';
            isValid = false;
        } else {
            userDescription.style.borderColor = '';
        }
    }

    // Display errors if any
    if (errors.length > 0 && errorContainer) {
        errorContainer.innerHTML = `<div style="color: red; border: 1px solid red; padding: 10px;">
                                    <p><strong>Please correct the following errors:</strong></p>
                                    <ul>${errors.map(error => `<li>${error}</li>`).join('')}</ul>
                                </div>`;
        errorContainer.style.display = 'block';
    } else if (errorContainer) {
        errorContainer.style.display = 'none'; // Hide the container if no errors
    }

    return isValid;
}

function validateSubscriptionOptions() {
    // Reset error display and outline colors if elements exist
    const errorContainer = document.getElementById('subscription-error');
    if (errorContainer) {
        errorContainer.style.display = 'none';
        errorContainer.innerHTML = '';
    }

    // Get all radio inputs with the name 'subscriptionOption'
    const subscriptionOptions = document.querySelectorAll('input[name="subscriptionOption"]');
    let isSelected = false;

    if (subscriptionOptions.length > 0) {
        // Check if any radio button is selected
        isSelected = Array.from(subscriptionOptions).some(radio => radio.checked);
        
        // If no option is selected, display error
        if (!isSelected) {
            if (errorContainer) {
                const errorText = `<p class="alert alert-danger">You must select a valid subscription.</p>`;
                errorContainer.innerHTML = errorText;
                errorContainer.style.display = 'block';
                errorContainer.innerHTML = `<div style="color: red; border: 1px solid red; padding: 10px;">
                                            <p><strong>Please correct the following errors:</strong></p>
                                            <ul>You must select a valid subscription.</ul>
                                            </div>`;
                errorContainer.style.display = 'block';
            }
        } else if (errorContainer) {
            errorContainer.style.display = 'none'; // Hide the container if no errors
        }
    }

    // Return true if a subscription is selected, otherwise false
    return isSelected;
}

function validatePaymentDetails() {
    // Reset error display and outline colors if elements exist
    const errorContainer = document.getElementById('cc-error');
    if (errorContainer) {
        errorContainer.style.display = 'none';
        errorContainer.innerHTML = '';
    }

    let isValid = true;
    const errors = [];

    // Validate Card Holder Name
    const cardName = document.getElementById('card-name');
    if (cardName && cardName.value.length < 5) {
        errors.push("Card Holder Name must be at least 5 characters long.");
        cardName.style.borderColor = 'red';
        isValid = false;
    } else if (cardName) {
        cardName.style.borderColor = '';
    }

    // Validate Billing Address
    const billingAddress = document.getElementById('billing-address');
    if (billingAddress && billingAddress.value.length < 10) {
        errors.push("Billing Address must be at least 10 characters long.");
        billingAddress.style.borderColor = 'red';
        isValid = false;
    } else if (billingAddress) {
        billingAddress.style.borderColor = '';
    }

    // Validate Country and State/Province
    const country = document.getElementById('billing-country');
    const state = document.getElementById('billing-state');
    const billingZip = document.getElementById('billing-zip');
    if (country) {
        if (country.selectedIndex === 0) {
            errors.push("Billing Country is required.");
            errors.push("Billing State/Province is required.");
            errors.push("Billing Postal Code/ZIP is invalid.");
            country.style.borderColor = 'red';
            state.style.borderColor = 'red';
            billingZip.style.borderColor = 'red';
            isValid = false;
        } else {
            country.style.borderColor = '';
            // Validate State/Province if country is selected
            if (state.selectedIndex === 0) {
                errors.push("Billing State/Province is required.");
                state.style.borderColor = 'red';
                isValid = false;
            } else {
                state.style.borderColor = '';
            }
        }
    }

    // Validate Postal Code based on selected Country
    let zipPattern;
    if (country.selectedIndex > 0) {
        const countryCode = country.value;
        if (countryCode === "USA") {
            zipPattern = /^\d{5}$/;
        } else if (countryCode === "CAN") {
            zipPattern = /^[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d$/;
        }

        if (zipPattern && !zipPattern.test(billingZip.value.replace(/\s/g, ''))) {
            errors.push("Billing Postal Code/ZIP is invalid for the selected country.");
            billingZip.style.borderColor = 'red';
            isValid = false;
        } else {
            billingZip.style.borderColor = '';
        }
    }

    // Check if Stripe Elements are complete and apply visual feedback
    function checkStripeElement(elementId, errorMessage) {
        const element = document.querySelector(elementId);
        if (!element.classList.contains('StripeElement--complete')) {
            errors.push(errorMessage);
            element.classList.add('StripeElement--error'); // Custom class for styling errors
            isValid = false;
        } else {
            element.classList.remove('StripeElement--error');
        }
    }

    checkStripeElement('#card-number-element', "Card number is incomplete.");
    checkStripeElement('#card-expiry-element', "Card expiry date is incomplete.");
    checkStripeElement('#card-cvc-element', "Card CVC is incomplete.");

    // Display errors if any
    if (errors.length > 0 && errorContainer) {
        errorContainer.innerHTML = `<div style="color: red; border: 1px solid red; padding: 10px;">
                                    <p><strong>Please correct the following errors:</strong></p>
                                    <ul>${errors.map(error => `<li>${error}</li>`).join('')}</ul>
                                </div>`;
        errorContainer.style.display = 'block';
    } else if (errorContainer) {
        errorContainer.style.display = 'none'; // Hide the container if no errors
    }

    return isValid;
}

function validateStripeDetails(callback) {
    // Assuming you have references to all necessary Stripe elements
    var cardNumberElement = elements.getElement('cardNumber');
    var cardExpiryElement = elements.getElement('cardExpiry');
    var cardCvcElement = elements.getElement('cardCvc');

    if (cardNumberElement._complete && cardExpiryElement._complete && cardCvcElement._complete) {
        stripe.createToken(cardNumberElement).then(function(result) {
            if (result.error) {
                // Handle the error, display it to the user
                const errorContainer = document.getElementById('cc-error');
                errorContainer.textContent = result.error.message;
                errorContainer.style.display = 'block';
                callback(false);
            } else {
                // Append the Stripe token to the form
                const form = document.getElementById('subscribe-form');
                const hiddenInput = document.createElement('input');
                hiddenInput.setAttribute('type', 'hidden');
                hiddenInput.setAttribute('name', 'stripeToken');
                hiddenInput.setAttribute('value', result.token.id);
                form.appendChild(hiddenInput);
                callback(true);
            }
        });
    } else {
        // Handle the case where not all elements are complete
        const errorContainer = document.getElementById('cc-error');
        errorContainer.textContent = "Please fill out all card details correctly.";
        errorContainer.style.display = 'block';
        callback(false);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('submit-sms-subscribe');
    if (submitButton) {
        submitButton.addEventListener('click', function(event) {
            event.preventDefault();

            const isValidAssistant = validateAssistantDetails();
            const isValidPersonal = validatePersonalPreferences();
            const isValidSubscription = validateSubscriptionOptions();
            const isValidPayment = validatePaymentDetails();

            if (isValidAssistant && isValidPersonal && isValidSubscription && isValidPayment) {
                validateStripeDetails(function(isValidStripe) {
                    if (isValidStripe) {
                        document.getElementById('subscribe-form').submit();
                    }
                });
            }
        });
    }
});

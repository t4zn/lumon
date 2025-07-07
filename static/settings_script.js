// settings_script.js
// Country dropdown and user profile update logic for settings page

const countryBtn = document.querySelector('.country-btn');
const countryDropdown = document.getElementById('country-dropdown');
const countryList = document.getElementById('country-list');
const countrySearch = document.getElementById('country-search');
const selectedCountrySpan = document.getElementById('selected-country');

const countries = [
  'United States', 'India', 'United Kingdom', 'Germany', 'France', 'Canada',
  'Australia', 'Brazil', 'Japan', 'China', 'South Africa', 'Russia', 'Mexico',
  'Italy', 'Spain', 'Turkey', 'Netherlands', 'Switzerland', 'Sweden', 'Norway', 'Denmark', 'Finland', 'Poland', 'Greece', 'Portugal', 'Singapore', 'Malaysia', 'Indonesia', 'Thailand', 'Vietnam', 'Philippines', 'South Korea', 'New Zealand', 'Argentina', 'Chile', 'Colombia', 'Peru', 'Egypt', 'Nigeria', 'Kenya', 'Morocco', 'Saudi Arabia', 'UAE', 'Qatar', 'Israel', 'Pakistan', 'Bangladesh', 'Sri Lanka', 'Nepal', 'Afghanistan', 'Ukraine', 'Czech Republic', 'Hungary', 'Romania', 'Belgium', 'Austria', 'Ireland', 'Croatia', 'Slovakia', 'Slovenia', 'Bulgaria', 'Estonia', 'Latvia', 'Lithuania', 'Iceland', 'Luxembourg', 'Liechtenstein', 'Monaco', 'Malta', 'Cyprus', 'Georgia', 'Armenia', 'Azerbaijan', 'Kazakhstan', 'Uzbekistan', 'Kyrgyzstan', 'Tajikistan', 'Turkmenistan', 'Mongolia', 'Cambodia', 'Laos', 'Myanmar', 'Brunei', 'East Timor', 'Fiji', 'Papua New Guinea', 'Solomon Islands', 'Vanuatu', 'Samoa', 'Tonga', 'Tuvalu', 'Nauru', 'Palau', 'Micronesia', 'Marshall Islands', 'Kiribati', 'Bahamas', 'Barbados', 'Belize', 'Dominica', 'Grenada', 'Guyana', 'Haiti', 'Jamaica', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Suriname', 'Trinidad and Tobago', 'Antigua and Barbuda', 'Saint Pierre and Miquelon', 'Greenland', 'Faroe Islands', 'Gibraltar', 'Bermuda', 'Cayman Islands', 'Falkland Islands', 'Montserrat', 'Saint Helena', 'Turks and Caicos Islands', 'British Virgin Islands', 'Anguilla', 'Aruba', 'Bonaire', 'Curacao', 'Saba', 'Sint Eustatius', 'Sint Maarten', 'Saint Barthelemy', 'Saint Martin', 'Guadeloupe', 'Martinique', 'French Guiana', 'Mayotte', 'Reunion', 'Wallis and Futuna', 'New Caledonia', 'French Polynesia']

function populateCountries() {
  countryList.innerHTML = '';
  countries.forEach(country => {
    const div = document.createElement('div');
    div.className = 'country-option';
    div.textContent = country;
    div.onclick = () => selectCountry(country);
    countryList.appendChild(div);
  });
}

function filterCountries() {
  const query = countrySearch.value.toLowerCase();
  const options = countryList.querySelectorAll('.country-option');
  options.forEach(option => {
    option.style.display = option.textContent.toLowerCase().includes(query) ? '' : 'none';
  });
}

function toggleCountryDropdown() {
  countryDropdown.style.display = countryDropdown.style.display === 'block' ? 'none' : 'block';
  if (countryDropdown.style.display === 'block') {
    countrySearch.focus();
  }
}

function selectCountry(country) {
  selectedCountrySpan.textContent = country;
  countryDropdown.style.display = 'none';
  // Save to backend
  fetch('/api/user/update_country', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ country })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showToast('Country updated!', 'success');
      } else {
        showToast('Failed to update country', 'error');
      }
    })
    .catch(() => showToast('Network error', 'error'));
}

// Close dropdown when clicking outside
window.addEventListener('click', function(e) {
  if (!countryDropdown.contains(e.target) && !countryBtn.contains(e.target)) {
    countryDropdown.style.display = 'none';
  }
});

if (countryBtn && countryDropdown && countryList && countrySearch && selectedCountrySpan) {
  populateCountries();
  countrySearch.addEventListener('keyup', filterCountries);
}

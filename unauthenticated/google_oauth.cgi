#!/usr/bin/perl
# google_oauth.cgi
# Handles Google OAuth2 redirect and callback authentication

use strict;
use warnings;
require '../web-lib.pl';
our (%text, %in, %gconfig, $config_directory);

&init_config();
&ReadParse();

# Load OAuth configuration from the aihelp module config
my %cfg;
&read_file("$config_directory/aihelp/config", \%cfg);

my $client_id = $cfg{'google_client_id'};
my $client_secret = $cfg{'google_client_secret'};
my $enabled = $cfg{'google_auth_enabled'};

if (!$enabled || !$client_id || !$client_secret) {
    &error("Google Authentication is not enabled or not fully configured.");
}

my $ssl = lc(get_env('https')) eq 'on' ? 1 : 0;
my $proto = $ssl ? "https" : "http";
my $redirect_uri = "$proto://$ENV{'HTTP_HOST'}/unauthenticated/google_oauth.cgi";

if ($in{'login'}) {
    # 1. Redirect to Google Auth endpoint
    my $state = &generate_random_id();
    
    # Store state in session cookie to verify on callback
    my $sec = $ssl ? "; secure" : "";
    $sec .= "; httpOnly" if (!$gconfig{'no_httponly'});
    $sec .= "; SameSite=Lax" if (!$gconfig{'no_samesite'});
    
    print "Set-Cookie: google_oauth_state=$state; path=/unauthenticated$sec\r\n";
    
    my $auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" .
                   "client_id=" . &urlize($client_id) .
                   "&redirect_uri=" . &urlize($redirect_uri) .
                   "&response_type=code" .
                   "&scope=openid%20email%20profile" .
                   "&state=" . &urlize($state);
    
    print "Location: $auth_url\r\n\r\n";
    exit;
}

if ($in{'code'}) {
    # 2. Verify state from cookie
    my $cookie_state = "";
    if ($ENV{'HTTP_COOKIE'} =~ /google_oauth_state=([a-f0-9]+)/) {
        $cookie_state = $1;
    }
    
    # Clear state cookie
    my $sec = $ssl ? "; secure" : "";
    $sec .= "; httpOnly" if (!$gconfig{'no_httponly'});
    print "Set-Cookie: google_oauth_state=; path=/unauthenticated; expires=Thu, 01-Jan-1970 00:00:00 GMT$sec\r\n";
    
    if (!$cookie_state || $in{'state'} ne $cookie_state) {
        &error("Invalid OAuth state parameter. Possible CSRF attack.");
    }
    
    my $code = $in{'code'};
    
    # 3. Exchange authorization code for ID token
    my $token_payload = "code=" . &urlize($code) .
                        "&client_id=" . &urlize($client_id) .
                        "&client_secret=" . &urlize($client_secret) .
                        "&redirect_uri=" . &urlize($redirect_uri) .
                        "&grant_type=authorization_code";
    
    my $token_body = "";
    my $token_err = "";
    my $token_ok = &http_post("oauth2.googleapis.com", 443, "/token", $token_payload, \$token_body, \$token_err, undef, 1, undef, undef, 15, 0, 1, { 'Content-Type' => 'application/x-www-form-urlencoded' });
    
    if (!$token_ok) {
        &error("Failed to exchange code: " . ($token_err || $token_body));
    }
    
    my $token_resp = &convert_from_json($token_body);
    my $id_token = $token_resp->{'id_token'};
    if (!$id_token) {
        &error("Google response did not contain ID Token.");
    }
    
    # 4. Verify ID token with Google TokenInfo API
    my $info_payload = "id_token=" . &urlize($id_token);
    my $info_body = "";
    my $info_err = "";
    my $info_ok = &http_post("oauth2.googleapis.com", 443, "/tokeninfo", $info_payload, \$info_body, \$info_err, undef, 1, undef, undef, 15, 0, 1, { 'Content-Type' => 'application/x-www-form-urlencoded' });
    
    if (!$info_ok) {
        &error("Failed to verify ID token: " . ($info_err || $info_body));
    }
    
    my $user_info = &convert_from_json($info_body);
    if ($user_info->{'aud'} ne $client_id) {
        &error("Audience mismatch in Google ID Token.");
    }
    if ($user_info->{'email_verified'} ne 'true' && $user_info->{'email_verified'} ne 1) {
        &error("Google email is not verified.");
    }
    
    my $email = $user_info->{'email'};
    if (!$email) {
        &error("No email address returned from Google.");
    }
    
    # 5. Domain mapping check
    my ($domain) = $email =~ /\@([^@]+)$/;
    my $allowed_domains_str = $cfg{'google_allowed_domains'} || "";
    my @allowed_domains = split(/\s*,\s*/, lc($allowed_domains_str));
    my $domain_ok = 0;
    foreach my $d (@allowed_domains) {
        if ($d eq lc($domain)) {
            $domain_ok = 1;
            last;
        }
    }
    if (!@allowed_domains || !$domain_ok) {
        &error("The email domain '$domain' is not allowed to log in.");
    }
    
    # 6. Map to local Webmin user
    my ($uname_prefix) = $email =~ /^([^@]+)/;
    my $mapped_user = "";
    
    &foreign_require("acl", "acl-lib.pl");
    my @users = &acl::list_users();
    my ($matching_user) = grep { lc($_->{'name'}) eq lc($uname_prefix) } @users;
    
    if ($matching_user) {
        $mapped_user = $matching_user->{'name'};
    } else {
        $mapped_user = $cfg{'google_default_user'} || "admin";
        my ($default_exists) = grep { lc($_->{'name'}) eq lc($mapped_user) } @users;
        if (!$default_exists) {
            &error("Default mapped user '$mapped_user' does not exist in AEL-WebMin.");
        }
    }
    
    # 7. Create Login Session
    my %miniserv;
    &get_miniserv_config(\%miniserv);
    my $sid = &acl::create_session_user(\%miniserv, $mapped_user);
    if (!$sid) {
        &error("Failed to generate login session for $mapped_user.");
    }
    
    my $sidname = $miniserv{'sidname'} || "sid";
    my $cpath = $miniserv{'cookiepath'} || "/";
    my $sec_cookie = $ssl ? "; secure" : "";
    $sec_cookie .= "; httpOnly" if (!$miniserv{'no_httponly'});
    $sec_cookie .= "; SameSite=Lax" if (!$miniserv{'no_samesite'});
    
    # Write session cookie and redirect to Webmin dashboard
    print "Set-Cookie: $sidname=$sid; path=$cpath$sec_cookie\r\n";
    print "Location: /\r\n\r\n";
    exit;
}

&error("Invalid callback request.");

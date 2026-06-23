#!/usr/bin/perl
# save_config.cgi
# Save settings for the AI Help Chatbot and Google OAuth2 module

use strict;
use warnings;
require '../web-lib.pl';
require './aihelp-lib.pl';
our (%text, %in, %config);

&init_config();
&ReadParse();

if ($in{'clear_key'}) {
    my %cfg = &get_config();
    delete($cfg{'gemini_api_key'});
    delete($cfg{'google_auth_enabled'});
    delete($cfg{'google_client_id'});
    delete($cfg{'google_client_secret'});
    delete($cfg{'google_allowed_domains'});
    delete($cfg{'google_default_user'});
    &save_config(\%cfg);
    &redirect("index.cgi");
}
else {
    my %cfg = &get_config();
    
    # 1. Gemini Settings
    my $key = $in{'gemini_api_key'};
    $key =~ s/^\s+//;
    $key =~ s/\s+$//;
    if (!$key) {
        &error($text{'index_err_key'});
    }
    $cfg{'gemini_api_key'} = $key;
    
    # 2. Google OAuth Settings
    $cfg{'google_auth_enabled'} = $in{'google_auth_enabled'} ? 1 : 0;
    
    my $client_id = $in{'google_client_id'};
    $client_id =~ s/^\s+//; $client_id =~ s/\s+$//;
    $cfg{'google_client_id'} = $client_id;
    
    my $client_secret = $in{'google_client_secret'};
    $client_secret =~ s/^\s+//; $client_secret =~ s/\s+$//;
    if ($client_secret ne "") {
        # Only save if changed (it's a password field, blank means keep existing)
        $cfg{'google_client_secret'} = $client_secret;
    }
    
    my $domains = $in{'google_allowed_domains'};
    $domains =~ s/^\s+//; $domains =~ s/\s+$//;
    $cfg{'google_allowed_domains'} = $domains;
    
    my $def_user = $in{'google_default_user'};
    $def_user =~ s/^\s+//; $def_user =~ s/\s+$//;
    $cfg{'google_default_user'} = $def_user || "admin";
    
    &save_config(\%cfg);
    &redirect("index.cgi");
}

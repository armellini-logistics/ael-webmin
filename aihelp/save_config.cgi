#!/usr/bin/perl
# save_config.cgi
# Save settings for the AI Help Chatbot module

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
    &save_config(\%cfg);
    &redirect("index.cgi");
}
else {
    my $key = $in{'gemini_api_key'};
    $key =~ s/^\s+//;
    $key =~ s/\s+$//;
    if (!$key) {
        &error($text{'index_err_key'});
    }
    my %cfg = &get_config();
    $cfg{'gemini_api_key'} = $key;
    &save_config(\%cfg);
    &redirect("index.cgi");
}

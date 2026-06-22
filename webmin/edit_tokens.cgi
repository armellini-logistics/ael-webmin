#!/usr/local/bin/perl
# edit_tokens.cgi
# Display active RPC tokens and allow generating new ones

use strict;
use warnings;
no warnings 'redefine';
no warnings 'uninitialized';
require './webmin-lib.pl';
our (%text, %in, %gconfig);
&ReadParse();

&ui_print_header(undef, $text{'tokens_title'}, "");

# Read existing tokens from config directory
my $tokens_file;
if ($main::miniserv_config_file =~ /^(.*)\/[^\/]+$/) {
	$tokens_file = "$1/rpc_tokens.conf";
} else {
	$tokens_file = "/etc/webmin/rpc_tokens.conf";
}

my %tokens;
if (-r $tokens_file) {
	&read_file($tokens_file, \%tokens);
}

# Print description
print $text{'tokens_desc'}, "<p>\n";

# If any token was recently created, display it in a success alert
if ($in{'created'}) {
	print &ui_alert_box(&text('tokens_created', "<tt>".&html_escape($in{'created'})."</tt>"), 'success');
}

# Form to list/delete existing tokens
if (keys %tokens) {
	my @tds = ( "width=5", "width=30%", "width=20%", "" );
	print &ui_form_start("save_tokens.cgi", "post");
	print &ui_hidden("action", "delete");
	
	my @table;
	foreach my $t (keys %tokens) {
		my ($user, $desc) = split(/:/, $tokens{$t}, 2);
		# url decode the description
		$desc =~ s/\+/ /g;
		$desc =~ s/%([0-9a-fA-F]{2})/pack("C", hex($1))/ge;
		
		# Truncate token value for display but keep checkbox name complete
		my $display_token = length($t) > 16 ? substr($t, 0, 16) . "..." : $t;
		push(@table, [
			&ui_checkbox("dtoken", $t),
			"<tt>" . &html_escape($display_token) . "</tt>",
			&html_escape($user),
			&html_escape($desc)
		]);
	}
	print &ui_columns_table(
		[ "", $text{'tokens_token'}, $text{'tokens_user'}, $text{'tokens_comment'} ],
		100,
		\@table,
		\@tds
	);
	print &ui_form_end([ [ "delete", $text{'tokens_delete'} ] ]);
} else {
	print "<b>$text{'tokens_none'}</b><p>\n";
}

print &ui_hr();

# Form to create a new token
&foreign_require("acl", "acl-lib.pl");
my @users = &acl::list_users();

print &ui_form_start("save_tokens.cgi", "post");
print &ui_hidden("action", "create");
print &ui_table_start($text{'tokens_add'}, undef, 2);

# Dropdown of users
print &ui_table_row(
	$text{'tokens_user_sel'},
	&ui_select("user", undef, [ map { $_->{'name'} } @users ])
);

# Token generation / custom token
my $qtlbl = &quote_escape($text{'tokens_token'}, '"');
print &ui_table_row(
	$text{'tokens_token'},
	&ui_radio("token_mode", 0, [
		[ 0, "$text{'tokens_gen'}<br>" ],
		[ 1, $text{'edit_token'} . " " . &ui_textbox("custom_token", undef, 35, undef, undef, "aria-label=\"$qtlbl\" placeholder=\"$qtlbl\"") ]
	])
);

# Description / Notes
print &ui_table_row(
	$text{'tokens_comment'},
	&ui_textbox("comment", undef, 50)
);

print &ui_table_end();
print &ui_form_end([ [ "create", $text{'save'} ] ]);

&ui_print_footer("", $text{'index_return'});

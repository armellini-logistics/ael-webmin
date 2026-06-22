#!/usr/local/bin/perl
# save_tokens.cgi
# Handles creating or deleting RPC authentication tokens

use strict;
use warnings;
no warnings 'redefine';
no warnings 'uninitialized';
require './webmin-lib.pl';
our (%text, %in, %gconfig);
&ReadParse();

&error_setup($text{'tokens_save_err'});

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

if ($in{'action'} eq 'create') {
	# Validate user
	my $user = $in{'user'};
	$user =~ /\S/ || &error($text{'tokens_err_user'});

	# Determine or generate token
	my $token;
	if ($in{'token_mode'} == 0) {
		# Generate secure random 32-char hex token
		if (open(my $fh, "/dev/urandom")) {
			my $buf;
			read($fh, $buf, 16);
			close($fh);
			$token = lc(unpack('h*', $buf));
		} else {
			$token = sprintf("%08x%08x%08x%08x", rand(0xffffffff), rand(0xffffffff), rand(0xffffffff), rand(0xffffffff));
		}
	} else {
		$token = $in{'custom_token'};
		$token =~ s/^\s+|\s+$//g;
		$token =~ /^\S+$/ || &error($text{'tokens_err_token'});
		$token !~ /=/ || &error($text{'tokens_err_token'});
	}

	# URL encode the comment/description
	my $desc = &urlize($in{'comment'});

	# Save token
	$tokens{$token} = "$user:$desc";

	&lock_file($tokens_file);
	&write_file($tokens_file, \%tokens);
	&set_ownership_permissions(undef, undef, 0600, $tokens_file);
	&unlock_file($tokens_file);

	&webmin_log("create", "token", $token, { 'user' => $user, 'desc' => $in{'comment'} });

	&redirect("edit_tokens.cgi?created=" . &urlize($token));
}
elsif ($in{'action'} eq 'delete') {
	# Delete selected tokens
	my @dtokens = split(/\0/, $in{'dtoken'});
	@dtokens || &error($text{'delete_enone'});

	foreach my $dt (@dtokens) {
		delete($tokens{$dt});
	}

	&lock_file($tokens_file);
	&write_file($tokens_file, \%tokens);
	&set_ownership_permissions(undef, undef, 0600, $tokens_file);
	&unlock_file($tokens_file);

	foreach my $dt (@dtokens) {
		&webmin_log("delete", "token", $dt);
	}

	&redirect("edit_tokens.cgi");
}
else {
	&error("Invalid action");
}

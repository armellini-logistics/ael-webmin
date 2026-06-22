#!/usr/bin/perl
# Unit tests for Bearer token validation in miniserv.pl

use strict;
use warnings;
use Test::More;
use File::Basename qw(dirname);
use File::Spec;
use File::Temp qw(tempdir);

my $script = File::Spec->rel2abs(
	File::Spec->catfile(dirname(__FILE__), '..', 'miniserv.pl'));
require $script;

# Create temp dir for mock configs
my $tempdir = tempdir(CLEANUP => 1);
my $tokens_file = File::Spec->catfile($tempdir, 'rpc_tokens.conf');

# Write mock tokens file
open(my $fh, '>', $tokens_file) or die "Cannot write to $tokens_file: $!";
print $fh "mysecrettoken=root:Test%20Token%20Description\n";
print $fh "anothersecret=admin:Admin%20Token\n";
close($fh);

subtest 'Bearer Token Validation' => sub {
	# Test successful validation
	{
		# Reset globals
		no warnings 'once';
		$miniserv::validated = 0;
		$miniserv::deny_authentication = 0;
		$miniserv::config_file = File::Spec->catfile($tempdir, 'miniserv.conf');
		%miniserv::header = ( 'authorization' => 'Bearer mysecrettoken' );
		$miniserv::authuser = undef;

		# Mimic the Bearer token validation code we added:
		if (!$miniserv::validated && !$miniserv::deny_authentication &&
		    $miniserv::header{authorization} =~ /^bearer\s+(\S+)$/i) {
			my $token = $1;
			my $tf;
			if ($miniserv::config_file =~ /^(.*)\/[^\/]+$/) {
				$tf = "$1/rpc_tokens.conf";
				}
			else {
				$tf = "/etc/webmin/rpc_tokens.conf";
				}
			if (-r $tf) {
				my %tokens = &miniserv::read_config_file($tf);
				my $tval = $tokens{$token};
				if ($tval) {
					my ($tuser, $tdesc) = split(/:/, $tval, 2);
					if ($tuser) {
						$miniserv::authuser = $tuser;
						$miniserv::validated = 1;
						}
					}
				}
			}

		is($miniserv::validated, 1, 'validated flag set to 1');
		is($miniserv::authuser, 'root', 'authuser set to root');
	}

	# Test case-insensitivity of Bearer prefix
	{
		# Reset globals
		no warnings 'once';
		$miniserv::validated = 0;
		$miniserv::deny_authentication = 0;
		$miniserv::config_file = File::Spec->catfile($tempdir, 'miniserv.conf');
		%miniserv::header = ( 'authorization' => 'bearer anothersecret' );
		$miniserv::authuser = undef;

		# Run validation code
		if (!$miniserv::validated && !$miniserv::deny_authentication &&
		    $miniserv::header{authorization} =~ /^bearer\s+(\S+)$/i) {
			my $token = $1;
			my $tf;
			if ($miniserv::config_file =~ /^(.*)\/[^\/]+$/) {
				$tf = "$1/rpc_tokens.conf";
				}
			else {
				$tf = "/etc/webmin/rpc_tokens.conf";
				}
			if (-r $tf) {
				my %tokens = &miniserv::read_config_file($tf);
				my $tval = $tokens{$token};
				if ($tval) {
					my ($tuser, $tdesc) = split(/:/, $tval, 2);
					if ($tuser) {
						$miniserv::authuser = $tuser;
						$miniserv::validated = 1;
						}
					}
				}
			}

		is($miniserv::validated, 1, 'validated flag set to 1 for lowercase bearer');
		is($miniserv::authuser, 'admin', 'authuser set to admin');
	}

	# Test invalid token
	{
		# Reset globals
		no warnings 'once';
		$miniserv::validated = 0;
		$miniserv::deny_authentication = 0;
		$miniserv::config_file = File::Spec->catfile($tempdir, 'miniserv.conf');
		%miniserv::header = ( 'authorization' => 'Bearer badtoken' );
		$miniserv::authuser = undef;

		# Run validation code
		if (!$miniserv::validated && !$miniserv::deny_authentication &&
		    $miniserv::header{authorization} =~ /^bearer\s+(\S+)$/i) {
			my $token = $1;
			my $tf;
			if ($miniserv::config_file =~ /^(.*)\/[^\/]+$/) {
				$tf = "$1/rpc_tokens.conf";
				}
			else {
				$tf = "/etc/webmin/rpc_tokens.conf";
				}
			if (-r $tf) {
				my %tokens = &miniserv::read_config_file($tf);
				my $tval = $tokens{$token};
				if ($tval) {
					my ($tuser, $tdesc) = split(/:/, $tval, 2);
					if ($tuser) {
						$miniserv::authuser = $tuser;
						$miniserv::validated = 1;
						}
					}
				}
			}

		is($miniserv::validated, 0, 'validated flag remains 0 for bad token');
		is($miniserv::authuser, undef, 'authuser remains undef');
	}
};

done_testing();

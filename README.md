
The Bugsnag agent forwards reports from your server to bugsnag.com or an
on-premise Bugsnag installation. It's used to avoid any latency impact that
might occur if you need to make a call over the network in every exception
handler.

## Getting started

First you need to download the `bugsnag-agent` from
[here](https://raw.github.com/bugsnag/bugsnag-agent/master/bin/bugsnag-agent)
and make it executable on your server. For example:

```bash
curl https://raw.github.com/bugsnag/bugsnag-agent/master/bin/bugsnag-agent | sudo tee /usr/bin/bugsnag-agent
chmod +x /usr/bin/bugsnag-agent
```

Next you need to run it.

```bash
$ bugsnag-agent
Bugsnag Agent started. http://127.0.0.1:3829 -> https://notify.bugsnag.com/
```

You can verify that it's running using curl in another terminal:

```bash
$ curl http://127.0.0.1:3829
Bugsnag agent: 127.0.0.1:4000 -> https://notify.bugsnag.com/ (0/1000)%
```

Finally you need to configure the endpoint of your Bugsnag apps to be `http://localhost:3829`. This differs per [notifier](https://bugsnag.com/docs/notifier), but for example PHP is:

```php
$bugsnag.setEndpoint("localhost:3829");
$bugsnag.setUseSSL(false);
```

## Upstart

If you'd like to ensure Bugsnag is always running, you can use the following `upstart` script:

```upstart
#!upstart
description "Bugsnag forwarding agent"
author      "Bugsnag <support@bugsnag.com>"

start on (filesystem and net-device-up IFACE=lo)
stop on shutdown

respawn
respawn limit 99 5

script
    exec bugsnag-agent 2>&1 1>/var/log/bugsnag.log
end script
```

## Configuration

`bugsnag-agent` reads /etc/bugsnag.conf by default. The default copy of this file is:

```conf
[bugsnag]

# The port to listen on.
port = 3829

# The interfact to listen on. Set this to 0.0.0.0 if you want to allow anyone
# to forward to Bugsnag. If you do that, ensure that this process is firewalled
# off from the global internet.
listen = 127.0.0.1

# The endpoint to send exceptions to. This can be another `bugsnag-agent`,
# https://notify.bugsnag.com/ or your local on-premise Bugsnag.
endpoint = https://notify.bugsnag.com/
```

You can change which configuration file is used with the `-c` parameter:

```
bugsnag-agent -c /usr/local/etc/bugsnag.conf
```

All the options can also be set directly using command line flags:

```
bugsnag-agent --port 3829 --listen 127.0.0.1 --endpoint https://notify.bugsnag.com/
```

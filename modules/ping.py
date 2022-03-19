"""
ping module for botty
"""

import subprocess


def ping(nick, source, privmsg, netmask, is_channel, send_message):
    """
    ping does a ping to the address provided
    """
    ret = None
    if privmsg.startswith(".ping "):
        ret = True
        cmd = privmsg[len(".ping ") :]
        cmd = cmd.split(" ")[0]
        if cmd.startswith("-"):
            return ret

        process = subprocess.run(
            ["ping", "-c", "4", "-i", "0.2", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if process.returncode == 0:
            for line in process.stdout.split("\n"):
                if line.strip() != "":
                    msg = line.strip()
        else:
            msg = process.stderr.strip()
            if msg == "":
                for line in process.stdout.split("\n"):
                    if line.strip() != "":
                        msg = line.strip()

        if msg.strip() != "":
            send_message(f"{msg}", source)

    return ret

import os
import jinja2
from datetime import date


C_HEADER_TEMPLATE = """#define VERSION     {{version}}
#define REVISION    {{revision}}
#define DATE        "{{date}}"
#define VERS        "{{app_name}} {{version}}.{{revision}}"
#define VSTRING     "{{app_name}} {{version}}.{{revision}} ({{date}})\\r\\n"
#define VERSTAG     "\\0$VER: {{app_name}} {{version}}.{{revision}} ({{date}})"
"""

ASM_INC_TEMPLATE = """VERSION		EQU	{{version}}
REVISION	EQU	{{revision}}

DATE	MACRO
		dc.b '{{date}}'
		ENDM

VERS	MACRO
		dc.b '{{app_name}} {{version}}.{{revision}}'
		ENDM

VSTRING	MACRO
		dc.b '{{app_name}} {{version}}.{{revision}} ({{date}})',13,10,0
		ENDM

VERSTAG	MACRO
		dc.b 0,'$VER: {{app_name}} {{version}}.{{revision}} ({{date}})',0
		ENDM
"""

def bumprev(version, appname):
    # Step 1. check for <appname>_rev.rev, <appname>_rev.h and <appname>_rev.i
    if not appname.endswith('_rev'):
        appname = appname + '_rev'

    rev_file = "%s.rev" % appname
    h_file = "%s.h" % appname
    i_file = "%s.i" % appname

    if os.path.exists(rev_file):
        with open(rev_file) as infile:
            line = infile.readline()
            revision = int(line.strip())
            revision += 1
    else:
        print("bumprev: creating new file \"%s\"" % rev_file)
        revision = 1

    with open(rev_file, "w") as outfile:
        outfile.write("%d" % revision)

    today = date.today()
    date_str = today.strftime("%d.%m.%Y")
    config = {
        "app_name": appname.replace("_rev", ""),
        "version": version,
        "revision": revision,
        "date": date_str
    }
    ch_templ = jinja2.Template(C_HEADER_TEMPLATE)
    with open(h_file, "w") as outfile:
        outfile.write(ch_templ.render(config))

    ai_templ = jinja2.Template(ASM_INC_TEMPLATE)
    with open(i_file, "w") as outfile:
        outfile.write(ai_templ.render(config))

    print("bumprev: bumped %s to revision %d" % (appname, revision))

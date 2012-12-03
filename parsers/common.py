class ParsingError(ValueError): pass


def parse_instructions(parser, arch, lines):
    # filter out instructions and parse them
    instructions = []
    for line in lines:
        line = line.strip()
        if not line.startswith('//') and not line == '' and not line.startswith('['):
            try:
                instructions.append(parser.parse_line(arch, line))
            except ParsingError, e:
                #print e, 'line skipped'
                pass
    return instructions

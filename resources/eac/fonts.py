from library.read_blocks.array import ArrayBlock
from library.read_blocks.atomic import IntegerBlock, Utf8Block
from library.read_blocks.compound import CompoundBlock
from resources.eac.bitmaps import Bitmap4Bit


class SymbolDefinitionRecord(CompoundBlock):
    class Fields(CompoundBlock.Fields):
        code = IntegerBlock(static_size=2, description='Code of symbol')
        glyph_width = IntegerBlock(static_size=1, description='Width of symbol in font bitmap')
        glyph_height = IntegerBlock(static_size=1, description='Height of symbol in font bitmap')
        glyph_x = IntegerBlock(static_size=2, description='Position (x) of symbol in font bitmap')
        glyph_y = IntegerBlock(static_size=2, description='Position (Y) of symbol in font bitmap')
        x_advance = IntegerBlock(static_size=1, description='Gap between this symbol and next one in rendered text')
        x_offset = IntegerBlock(static_size=1, is_signed=True, description='Offset (x) for drawing the character image')
        y_offset = IntegerBlock(static_size=1, is_signed=True, description='Offset (y) for drawing the character image')


class FfnFont(CompoundBlock):
    class Fields(CompoundBlock.Fields):
        resource_id = Utf8Block(required_value='FNTF', length=4, description='Resource ID')
        file_size = IntegerBlock(static_size=4, description='This file size in bytes')
        unknowns0 = ArrayBlock(length=2, child=IntegerBlock(static_size=1))
        symbols_amount = IntegerBlock(static_size=2, description='Amount of symbols, defined in this font')
        unknowns1 = ArrayBlock(length=16, child=IntegerBlock(static_size=1))
        bitmap_data_pointer = IntegerBlock(static_size=2, description='Pointer to bitmap block')
        unknowns2 = ArrayBlock(length=2, child=IntegerBlock(static_size=1))
        definitions = ArrayBlock(child=SymbolDefinitionRecord(), length_label='symbols_amount',
                                 description='Definitions of chars in this bitmap font')
        skip_bytes = ArrayBlock(length_label='up to offset bitmap_data_pointer', child=IntegerBlock(static_size=1, required_value=0xAD),
                                description='4-bytes AD AD AD AD (optional, happens in nfs2 SWISS36)')
        bitmap = Bitmap4Bit(description='Font atlas bitmap data')
        
        unknown_fields = ['unknowns0', 'unknowns1', 'unknowns2']

    def _after_symbols_amount_read(self, data, state, **kwargs):
        if not state.get('definitions'):
            state['definitions'] = {}
        state['definitions']['length'] = data['symbols_amount'].value

    def _after_definitions_read(self, data, state, buffer, **kwargs):
        if not state.get('skip_bytes'):
            state['skip_bytes'] = {}
        state['skip_bytes']['length'] = data['bitmap_data_pointer'].value - buffer.tell()


import { resolveAsset } from 'tgui/assets';
import { useBackend } from 'tgui/backend';
import { Box, Image, Section, Stack } from 'tgui-core/components';
import type { ExaminePanelData } from './data';

export const FlavorTextPage = (props) => {
  const { data } = useBackend<ExaminePanelData>();
  const { headshot, flavor_text, ooc_notes } = data;

  const flavorHTML = {
    __html: `<span className='Chat'>${flavor_text}</span>`,
  };
  const oocHTML = {
    __html: `<span className='Chat'>${ooc_notes}</span>`,
  };

  return (
    <Stack fill>
      <Stack fill vertical>
        <Stack.Item align="center">
          {headshot && (
            <img src={resolveAsset(headshot)} width="350px" height="350px" />
          )}
        </Stack.Item>
        <Stack.Item grow>
          <Section scrollable fill title="OOC Notes" preserveWhitespace>
            <Box dangerouslySetInnerHTML={oocHTML} />
          </Section>
        </Stack.Item>
      </Stack>
      <Stack.Item grow>
        <Section scrollable fill preserveWhitespace title="Flavor Text">
          <Box dangerouslySetInnerHTML={flavorHTML} />
        </Section>
      </Stack.Item>
    </Stack>
  );
};

export const ImageGalleryPage = (props) => {
  const { data } = useBackend<ExaminePanelData>();
  const { img_gallery = [], ooc_extra_video } = data;

  return (
    <Section fill scrollable title="Gallery">
      <Stack fill vertical>
        {img_gallery.map((image) => (
          <Stack.Item grow key={image}>
            <Section align="center">
              <Image maxHeight="100%" maxWidth="100%" src={resolveAsset(image)} />
            </Section>
          </Stack.Item>
        ))}
        {ooc_extra_video && (
          <Stack.Item grow>
            <Section align="center">
              <video
                controls
                preload="metadata"
                src={ooc_extra_video}
                style={{ maxWidth: '100%', maxHeight: '100%' }}
              />
            </Section>
          </Stack.Item>
        )}
        {!img_gallery.length && !ooc_extra_video && 'No media in this gallery!'}
      </Stack>
    </Section>
  );
};

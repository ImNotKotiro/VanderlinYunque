import { useMemo, useState } from 'react';
import { resolveAsset } from 'tgui/assets';
import { useBackend } from 'tgui/backend';
import { Box, Button, Section, Stack } from 'tgui-core/components';
import { Window } from 'tgui/layouts';
import type { ExaminePanelData } from './data';

export const ExaminePanel = (props) => {
  const { data } = useBackend<ExaminePanelData>();
  const { character_name, headshot, flavor_text, ooc_notes, ooc_extra_link, descriptor_text } = data;
  const [page, setPage] = useState<'profile' | 'gallery'>('profile');
  const [audioOpen, setAudioOpen] = useState(false);

  const mediaExtension = useMemo(() => {
    if (!ooc_extra_link) return '';
    const cleanUrl = ooc_extra_link.split(/[?#]/)[0].toLowerCase();
    const parts = cleanUrl.split('.');
    return parts.length > 1 ? parts[parts.length - 1] : '';
  }, [ooc_extra_link]);

  const isImage = ['jpg', 'jpeg', 'png', 'gif'].includes(mediaExtension);
  const isVideo = mediaExtension === 'mp4';
  const isAudio = mediaExtension === 'mp3';
  const hasGallery = isImage || isVideo;

  const flavorHTML = {
    __html: `<span className='Chat'>${flavor_text}</span>`,
  };
  const oocHTML = {
    __html: `<span className='Chat'>${ooc_notes}</span>`,
  };

  return (
    <Window
      title={character_name}
      width={1000}
      height={700}
      theme="grim"
      buttons={
        <>
          {hasGallery && (
            <Button
              icon="images"
              selected={page === 'gallery'}
              onClick={() => setPage(page === 'gallery' ? 'profile' : 'gallery')}
            >
              Gallery
            </Button>
          )}
          {isAudio && (
            <Button
              icon="music"
              selected={audioOpen}
              onClick={() => setAudioOpen(!audioOpen)}
            >
              OOC Audio
            </Button>
          )}
        </>
      }
    >
      <Window.Content>
        {page === 'gallery' && hasGallery ? (
          <Section fill scrollable title={isVideo ? 'Gallery — Video' : 'Gallery'}>
            <Stack fill justify="center" align="center">
              {isImage && (
                <img
                  src={resolveAsset(ooc_extra_link)}
                  style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                />
              )}
              {isVideo && (
                <video
                  controls
                  src={resolveAsset(ooc_extra_link)}
                  style={{ maxWidth: '100%', maxHeight: '100%' }}
                />
              )}
            </Stack>
          </Section>
        ) : (
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
              <Stack fill vertical>
                <Stack.Item>
                  <Section scrollable title="At First Glance" preserveWhitespace>
                    <Box dangerouslySetInnerHTML={{ __html: descriptor_text || "You see an ordinary person." }} />
                  </Section>
                </Stack.Item>
                <Stack.Item grow>
                  <Section scrollable fill preserveWhitespace title="Flavor Text">
                    <Box dangerouslySetInnerHTML={flavorHTML} />
                    {isAudio && audioOpen && (
                      <Box mt={1} textAlign="center">
                        <audio controls autoPlay src={resolveAsset(ooc_extra_link)} />
                      </Box>
                    )}
                  </Section>
                </Stack.Item>
              </Stack>
            </Stack.Item>
          </Stack>
        )}
      </Window.Content>
    </Window>
  );
};

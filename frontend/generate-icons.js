import sharp from 'sharp';
import { readFileSync } from 'fs';

const svgBuffer = readFileSync('public/favicon.svg');

async function generateIcons() {
  // 192x192 (minimum for Android installable PWA)
  await sharp(svgBuffer)
    .resize(192, 192)
    .png()
    .toFile('public/icon-192.png');
  console.log('✓ icon-192.png generated');

  // 512x512 (recommended for Android splash/launcher)
  await sharp(svgBuffer)
    .resize(512, 512)
    .png()
    .toFile('public/icon-512.png');
  console.log('✓ icon-512.png generated');

  // Maskable icon with safe zone padding
  const maskableSize = 512;
  const safeZoneRatio = 0.8;
  const iconSize = Math.floor(maskableSize * safeZoneRatio);
  const padding = Math.floor((maskableSize - iconSize) / 2);

  await sharp({
    create: {
      width: maskableSize,
      height: maskableSize,
      channels: 4,
      background: { r: 30, g: 58, b: 138, alpha: 1 },
    },
  })
    .composite([{
      input: await sharp(svgBuffer).resize(iconSize, iconSize).png().toBuffer(),
      top: padding,
      left: padding,
    }])
    .png()
    .toFile('public/icon-512-maskable.png');
  console.log('✓ icon-512-maskable.png generated');
}

generateIcons().catch(err => {
  console.error('Icon generation failed:', err);
  process.exit(1);
});

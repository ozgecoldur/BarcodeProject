import com.google.zxing.*;
import com.google.zxing.client.j2se.BufferedImageLuminanceSource;
import com.google.zxing.common.HybridBinarizer;
import com.google.zxing.multi.GenericMultipleBarcodeReader;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.Arrays;
import java.util.EnumMap;
import java.util.Map;

public class DecodeBarcode {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Kullanım: java DecodeBarcode <resim_yolu>");
            return;
        }

        try {
            File file = new File(args[0]);
            BufferedImage image = ImageIO.read(file);

            if (image == null) {
                System.out.println("Resim okunamadı. Dosya yolu doğru mu?");
                return;
            }

            LuminanceSource source = new BufferedImageLuminanceSource(image);
            BinaryBitmap bitmap = new BinaryBitmap(new HybridBinarizer(source));

            // 🔥 HINTS TANIMLANIYOR 🔥
            Map<DecodeHintType, Object> hints = new EnumMap<>(DecodeHintType.class);
            hints.put(DecodeHintType.POSSIBLE_FORMATS, Arrays.asList(
                    BarcodeFormat.CODE_128,
                    BarcodeFormat.EAN_13,
                    BarcodeFormat.EAN_8,
                    BarcodeFormat.UPC_A,
                    BarcodeFormat.UPC_E));
            hints.put(DecodeHintType.TRY_HARDER, Boolean.TRUE); // Opsiyonel ama önerilir

            MultiFormatReader baseReader = new MultiFormatReader();
            baseReader.setHints(hints); // 🔥 HINTS BURAYA UYGULANIYOR 🔥

            GenericMultipleBarcodeReader multiReader = new GenericMultipleBarcodeReader(baseReader);
            Result[] results = multiReader.decodeMultiple(bitmap);

            if (results == null || results.length == 0) {
                System.out.println("Hata: Barkod bulunamadı.");
                return;
            }

            for (Result result : results) {
                System.out.println("Parsed result: " + result.getText());
            }

        } catch (NotFoundException e) {
            System.out.println("Hata: Barkod bulunamadı.");
        } catch (Exception e) {
            System.out.println("Genel hata: " + e.getMessage());
            e.printStackTrace();
        }
    }
}

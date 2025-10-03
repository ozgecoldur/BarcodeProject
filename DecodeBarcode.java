import com.google.zxing.*;
import com.google.zxing.client.j2se.BufferedImageLuminanceSource;
import com.google.zxing.common.HybridBinarizer;
import com.google.zxing.multi.GenericMultipleBarcodeReader;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;

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

            MultiFormatReader baseReader = new MultiFormatReader();
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
// javac -cp "lib/core-3.5.3.jar;lib/javase-3.5.3.jar;lib/jcommander-1.81.jar;."
// DecodeBarcode.java
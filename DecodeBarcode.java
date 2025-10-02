import com.google.zxing.*;
import com.google.zxing.client.j2se.*;
import com.google.zxing.common.*;
import java.io.File;
import javax.imageio.ImageIO;

public class DecodeBarcode {
    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            System.out.println("Kullanım: java DecodeBarcode <resim_yolu>");
            return;
        }

        File file = new File(args[0]);
        BufferedImageLuminanceSource source = new BufferedImageLuminanceSource(ImageIO.read(file));
        BinaryBitmap bitmap = new BinaryBitmap(new HybridBinarizer(source));
        Result result = new MultiFormatReader().decode(bitmap);

        System.out.println("Parsed result: " + result.getText());
    }
}

import oscP5.*;

OscP5 _osc;

static int BUFFER_SIZE = 20;
int timber_num = 4;
float[][] timber_values = new float[timber_num][BUFFER_SIZE];
String[] timber_names = new String[timber_num];

float max_value = -1.0;

int[] color_list = {
    #FF0000, #00FF00, #0000FF, #FFFF00, #FF00FF, #00FFFF
};

void setup(){
    size(800, 600);
    frameRate(60);
    colorMode(RGB,256);
    _osc = new OscP5(this, 5000);

    for(int i = 0;i < timber_num; i++){
        timber_names[i] = "";
    }
}

void draw(){
    background(#000000);

    // プロット描画
    strokeWeight(1);
    stroke(#000000);
    fill(#FFFFFF);
    rect(50,100, 550, 400);
    for(int i = 0;i < timber_num;i++){
        strokeWeight(5);
        stroke(color_list[i]);
        for(int j = 0;j < BUFFER_SIZE-1;j++){
            line(
                80+520/BUFFER_SIZE*j,
                400-300*(timber_values[i][j]/max_value),
                80+520/BUFFER_SIZE*(j+1),
                400-300*(timber_values[i][j+1]/max_value)
            );
        }
    }

    // 音色名を表示
    textSize(24);
    for(int i = 0; i < timber_num; i++){
        fill(color_list[i]);
        text(timber_names[i], 600, 100 + 50*(i+1));
    }
}

void oscEvent(OscMessage msg){
    println(msg);
    if(msg.checkAddrPattern("/timber_size") == true) {
        timber_num = msg.get(0).intValue();
        timber_names = new String[timber_num];
        timber_values = new float[timber_num][BUFFER_SIZE];
        for(int i = 1;i < timber_num+1;i++){
            timber_names[i-1] = msg.get(i).stringValue();
        }
    }else if(msg.checkAddrPattern("/sep_data") == true) {
        max_value = 0;
        for(int i = 0;i < timber_num;i++){
            for(int j = 0;j < BUFFER_SIZE-1;j++){
                timber_values[i][j] = timber_values[i][j+1];
                if(max_value < timber_values[i][j]){
                    max_value = timber_values[i][j];
                }
            }
            timber_values[i][BUFFER_SIZE-1] = msg.get(i).floatValue();
            if(max_value < timber_values[i][BUFFER_SIZE-1]){
                max_value = timber_values[i][BUFFER_SIZE-1];
            }
        }
    }
}

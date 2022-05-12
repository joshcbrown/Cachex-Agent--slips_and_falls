for i in {3..15}
do 
    time=$( expr $i '*' "$i" )
    echo echo python -m referee $i abnt_edge abnear_trans -s 100 -t $time
    echo echo python -m referee $i abnear_trans abnt_edge -s 100 -t $time
done
